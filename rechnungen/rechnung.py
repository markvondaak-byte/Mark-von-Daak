#!/usr/bin/env python3
"""Rechnungen, Angebote, Quittungen und Stornos als PDF – ohne Online-Dienst.

Befehle (im Repository-Wurzelordner ausführen):

  python3 rechnungen/rechnung.py neu rechnung            # neue Rechnung aus Vorlage anlegen
  python3 rechnungen/rechnung.py neu angebot             # neues Angebot
  python3 rechnungen/rechnung.py bauen <beleg.yaml>      # PDF erzeugen (vergibt Nummer bei "auto")
  python3 rechnungen/rechnung.py umwandeln <angebot.yaml>  # Angebot -> Rechnung
  python3 rechnungen/rechnung.py storno <rechnung.yaml>  # Stornorechnung zur Rechnung
  python3 rechnungen/rechnung.py bezahlt <rechnung.yaml> [--datum 2026-12-01] [--art Überweisung]
  python3 rechnungen/rechnung.py liste [--jahr 2026]     # Übersicht + Ausgangsbuch (CSV)
  python3 rechnungen/rechnung.py archiv [--jahr 2026]    # alle PDFs + CSV als ZIP für die Steuer

Daten:
  rechnungen/absender.yaml   eigene Angaben (öffentlich, steht auch im Impressum)
  rechnungen/privat/bank.yaml Bankverbindung (gitignored)
  rechnungen/belege/*.yaml   deine Belege mit Kundendaten (gitignored)
  rechnungen/out/            fertige PDFs (gitignored)
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import sys
import zipfile
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

HIER = Path(__file__).resolve().parent
BELEGE = HIER / "belege"
OUT = HIER / "out"
PRIVAT = HIER / "privat"
VORLAGEN = HIER / "vorlagen"
KATALOGE = HIER / "kataloge"
ZAEHLER = HIER / "nummern.json"   # ohne Kundendaten, wird committet: Nummern laufen sitzungsübergreifend weiter

ARTEN = {
    "rechnung": "Rechnung",
    "angebot": "Angebot",
    "quittung": "Quittung",
    "storno": "Stornorechnung",
    "korrektur": "Rechnungskorrektur",
    "proforma": "Proforma-Rechnung",
    "lieferschein": "Lieferschein",
    "auftrag": "Auftragsbestätigung",
}
# Belege, die steuerlich als Rechnung zählen und ins Ausgangsbuch gehören
STEUERBELEGE = {"rechnung", "quittung", "storno", "korrektur"}

STEUERFAELLE = {
    "normal": "",
    "kleinunternehmer": "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.",
    "reverse_charge": "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge, § 13b UStG).",
    "ig_lieferung": "Steuerfreie innergemeinschaftliche Lieferung (§ 4 Nr. 1b i. V. m. § 6a UStG).",
    "drittland": "Leistung nicht im Inland steuerbar.",
}

D0 = Decimal("0.00")


# ----------------------------------------------------------------- Hilfen ---

def dec(x) -> Decimal:
    return Decimal(str(x if x not in (None, "") else 0))


def rund(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def geld(x: Decimal, waehrung: str = "EUR") -> str:
    s = f"{rund(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    zeichen = {"EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF"}.get(waehrung, waehrung)
    return f"{s} {zeichen}"


def zahl(x) -> str:
    d = dec(x).normalize()
    s = f"{d:f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


def datum(x) -> dt.date:
    if isinstance(x, dt.date):
        return x
    if not x or str(x).lower() == "heute":
        return dt.date.today()
    return dt.date.fromisoformat(str(x))


def de_datum(x) -> str:
    return datum(x).strftime("%d.%m.%Y")


def leistung_text(x) -> str:
    """'2026-11-27' -> 27.11.2026 · '2026-11' -> November 2026 · Freitext bleibt."""
    if isinstance(x, dt.date):
        return de_datum(x)
    s = str(x or "").strip()
    monate = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
              "September", "Oktober", "November", "Dezember"]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return de_datum(s)
    if m := re.fullmatch(r"(\d{4})-(\d{2})", s):
        return f"{monate[int(m[2]) - 1]} {m[1]}"
    return s


def esc(s) -> str:
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("\n", "<br/>"))


def lade_yaml(p: Path) -> dict:
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def lade_absender(profil: str | None = None) -> dict:
    a = lade_yaml(HIER / "absender.yaml")
    if profil:
        datei = HIER / f"absender-{profil}.yaml"
        if not datei.exists():
            sys.exit(f"Absenderprofil „{profil}“ fehlt ({datei.relative_to(HIER.parent)}).")
        a.update(lade_yaml(datei))
    bank = PRIVAT / "bank.yaml"
    a["bank"] = lade_yaml(bank) if bank.exists() else {}
    # Fallback für frische Cloud-Sitzungen: IBAN aus der Umgebung (nie im Repository)
    import os
    if not a["bank"].get("iban") and os.environ.get("RECHNUNG_IBAN"):
        a["bank"] = {"iban": os.environ["RECHNUNG_IBAN"], "bic": os.environ.get("RECHNUNG_BIC", ""),
                     "bank": os.environ.get("RECHNUNG_BANK", ""),
                     "kontoinhaber": os.environ.get("RECHNUNG_KONTOINHABER", a.get("inhaber") or a.get("name", ""))}
    return a


# ---------------------------------------------------------------- Schrift ---

def schriften() -> tuple[str, str, str]:
    """Inter als TrueType einbinden (OTF wird einmalig umgewandelt), sonst Liberation Sans."""
    cache = OUT / ".schriften"
    quelle = Path("/usr/share/fonts/opentype/inter")
    namen = {"Inter": "Inter-Regular", "Inter-Medium": "Inter-SemiBold", "Inter-Bold": "InterDisplay-Bold"}
    try:
        cache.mkdir(parents=True, exist_ok=True)
        for rl_name, datei in namen.items():
            ttf = cache / f"{datei}.ttf"
            if not ttf.exists():
                from fontTools.ttLib import TTFont as FT
                from fontTools.pens.cu2quPen import Cu2QuPen
                from fontTools.pens.ttGlyphPen import TTGlyphPen
                from fontTools.ttLib import newTable
                font = FT(str(quelle / f"{datei}.otf"))
                gs = font.getGlyphSet()
                glyf = newTable("glyf")
                glyf.glyphOrder = font.getGlyphOrder()
                glyf.glyphs = {}
                for g in glyf.glyphOrder:
                    pen = TTGlyphPen(None)
                    gs[g].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
                    glyf.glyphs[g] = pen.glyph()
                font["glyf"] = glyf
                font["loca"] = newTable("loca")
                font["maxp"].tableVersion = 0x00010000
                for k in ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs",
                          "maxInstructionDefs", "maxStackElements", "maxSizeOfInstructions",
                          "maxComponentElements", "maxPoints", "maxContours",
                          "maxCompositePoints", "maxCompositeContours", "maxComponentDepth"):
                    setattr(font["maxp"], k, 0)
                font["maxp"].maxZones = 1
                font["head"].glyphDataFormat = 0
                font["post"].formatType = 2.0
                font["post"].extraNames = []
                font["post"].mapping = {}
                font["post"].glyphOrder = glyf.glyphOrder
                del font["CFF "]
                if "VORG" in font:
                    del font["VORG"]
                font.sfntVersion = "\x00\x01\x00\x00"
                font.save(str(ttf))
            pdfmetrics.registerFont(TTFont(rl_name, str(ttf)))
        return "Inter", "Inter-Medium", "Inter-Bold"
    except Exception as e:  # Fallback ohne fontTools oder Inter
        print(f"Hinweis: Inter nicht nutzbar ({e}) – nehme Liberation Sans.", file=sys.stderr)
        lib = Path("/usr/share/fonts/truetype/liberation")
        pdfmetrics.registerFont(TTFont("LS", str(lib / "LiberationSans-Regular.ttf")))
        pdfmetrics.registerFont(TTFont("LS-Bold", str(lib / "LiberationSans-Bold.ttf")))
        return "LS", "LS-Bold", "LS-Bold"


# ---------------------------------------------------------- Nummernkreis ---

def naechste_nummer(art: str, absender: dict, jahr: int, verbrauchen: bool = True) -> str:
    muster = (absender.get("nummernkreise") or {}).get(art) or (art[:2].upper() + "-{jahr}-{nr:03d}")
    z = json.loads(ZAEHLER.read_text()) if ZAEHLER.exists() else {}
    schluessel = f"{art}-{jahr}"
    nr = z.get(schluessel, 0) + 1
    vorhandene = {b.get("nummer") for _, b in alle_belege()}
    while muster.format(jahr=jahr, nr=nr) in vorhandene:
        nr += 1
    if verbrauchen:
        z[schluessel] = nr
        ZAEHLER.write_text(json.dumps(z, indent=2, ensure_ascii=False))
    return muster.format(jahr=jahr, nr=nr)


def alle_belege():
    for p in sorted(BELEGE.glob("*.yaml")):
        try:
            yield p, lade_yaml(p)
        except Exception as e:
            print(f"Übersprungen: {p.name} ({e})", file=sys.stderr)


def schreibe_feld(p: Path, feld: str, wert: str) -> None:
    """Ein Feld in der YAML ersetzen, ohne Kommentare und Reihenfolge zu zerstören."""
    text = p.read_text(encoding="utf-8")
    neu, n = re.subn(rf"(?m)^{feld}:.*$", f"{feld}: {wert}", text, count=1)
    if not n:
        neu = f"{feld}: {wert}\n" + text
    p.write_text(neu, encoding="utf-8")


# ------------------------------------------------------------- Katalog ---

def lade_katalog(name: str) -> dict:
    p = KATALOGE / f"{name}.yaml"
    if not p.exists():
        sys.exit(f"Katalog „{name}“ nicht gefunden ({p.relative_to(HIER.parent)}).")
    return lade_yaml(p)


def finde_artikel(kat: dict, schluessel: str) -> dict | None:
    """Schlüssel, Alias oder Artikelnummer."""
    artikel = kat.get("artikel") or {}
    schluessel = (kat.get("aliase") or {}).get(schluessel, schluessel)
    if schluessel in artikel:
        return artikel[schluessel]
    return next((e for e in artikel.values() if str(e.get("artikelnr", "")) == schluessel.lstrip("#")), None)


def katalog_aufloesen(b: dict) -> dict:
    """Positionen mit 'artikel:' aus dem Katalog ergänzen (Angaben im Beleg haben Vorrang)."""
    positionen = b.get("positionen") or []
    if not any(isinstance(pos, dict) and pos.get("artikel") for pos in positionen):
        return b
    neu = []
    kataloge = {}
    for pos in positionen:
        if pos.get("artikel"):
            ref = str(pos["artikel"])
            name, _, schluessel = ref.rpartition("/")
            name = name or b.get("katalog")
            if not name:
                sys.exit(f"Artikel „{ref}“: Katalog fehlt (katalog: fitline oder artikel: fitline/{ref}).")
            kat = kataloge.setdefault(name, lade_katalog(name))
            eintrag = finde_artikel(kat, schluessel)
            if eintrag is None:
                sys.exit(f"Artikel „{schluessel}“ steht nicht im Katalog {name}. "
                         f"Liste: python3 rechnungen/rechnung.py artikel {name}")
            pos = {"ust": kat.get("standard_ust", 19), **eintrag, **{k: v for k, v in pos.items() if k != "artikel"}}
            if pos.get("preis") is None:
                sys.exit(f"Artikel „{schluessel}“ hat im Katalog {name} noch keinen Preis – bitte eintragen.")
        neu.append(pos)
    b = {**b, "positionen": neu}
    if "preise" not in b and kataloge:
        b["preise"] = next(iter(kataloge.values())).get("preise", "netto")
    return b


# ------------------------------------------------------------- Rechnen ---

def berechne(b: dict) -> dict:
    """Summen nach Steuersätzen. Preise netto (Standard) oder brutto (preise: brutto)."""
    b = katalog_aufloesen(b)
    steuerfall = b.get("steuerfall", "normal")
    ohne_ust = steuerfall != "normal"
    brutto_modus = str(b.get("preise", "netto")).lower() == "brutto"
    rabatt = dec(b.get("rabatt_prozent")) / 100
    zeilen, saetze = [], {}
    for i, pos in enumerate(b.get("positionen") or [], 1):
        menge = dec(pos.get("menge", 1))
        preis = dec(pos.get("preis"))
        satz = D0 if ohne_ust else dec(pos.get("ust", b.get("ust", 19)))
        betrag = rund(menge * preis)
        zeilen.append({**pos, "nr": i, "menge": menge, "preis": preis, "satz": satz, "betrag": betrag})
        saetze[satz] = saetze.get(satz, D0) + betrag
    gruppen = []
    for satz, summe in sorted(saetze.items(), reverse=True):
        abzug = rund(summe * rabatt)
        basis = summe - abzug
        if brutto_modus:
            netto = rund(basis / (1 + satz / 100))
            steuer = basis - netto
        else:
            netto = basis
            steuer = rund(netto * satz / 100)
        gruppen.append({"satz": satz, "summe": summe, "abzug": abzug, "netto": netto, "steuer": steuer})
    netto = sum((g["netto"] for g in gruppen), D0)
    steuer = sum((g["steuer"] for g in gruppen), D0)
    return {"zeilen": zeilen, "gruppen": gruppen, "netto": netto, "steuer": steuer,
            "brutto": netto + steuer, "brutto_modus": brutto_modus, "ohne_ust": ohne_ust,
            "positionen_summe": sum(saetze.values(), D0)}


def pruefe(b: dict, a: dict, art: str) -> list[str]:
    """Pflichtangaben nach § 14 Abs. 4 UStG prüfen (Warnungen, kein Abbruch)."""
    w = []
    e = b.get("empfaenger") or {}
    if art in STEUERBELEGE:
        if not (a.get("ust_id") or a.get("steuernummer")):
            w.append("Absender: USt-IdNr. oder Steuernummer fehlt.")
        if not (e.get("name") or e.get("firma")) or not e.get("plz_ort"):
            w.append("Empfänger: Name und vollständige Anschrift fehlen.")
        if not b.get("leistungsdatum") and art != "storno":
            w.append("Leistungsdatum/-zeitraum fehlt (Pflicht, auch wenn gleich Rechnungsdatum).")
        if b.get("steuerfall") == "reverse_charge" and not e.get("ust_id"):
            w.append("Reverse Charge: USt-IdNr. des Empfängers fehlt.")
        if b.get("steuerfall") == "kleinunternehmer" and not a.get("kleinunternehmer"):
            w.append("Steuerfall Kleinunternehmer, aber absender.yaml sagt kleinunternehmer: false.")
        if art in ("storno", "korrektur") and not b.get("bezug"):
            w.append("Storno/Korrektur: Bezug auf die ursprüngliche Rechnung (bezug:) fehlt.")
    if not b.get("positionen"):
        w.append("Keine Positionen.")
    return w


# ---------------------------------------------------------- Girocode-QR ---

def girocode(bank: dict, betrag: Decimal, zweck: str, name: str) -> Drawing | None:
    """EPC-QR-Code: Banking-Apps übernehmen IBAN, Betrag und Verwendungszweck."""
    iban = str(bank.get("iban", "")).replace(" ", "")
    if not iban or betrag <= 0:
        return None
    daten = "\n".join(["BCD", "002", "1", "SCT", str(bank.get("bic", "")).replace(" ", ""),
                       (bank.get("kontoinhaber") or name)[:70], iban, f"EUR{rund(betrag)}",
                       "", "", zweck[:140]])
    w = QrCodeWidget(daten, barLevel="M")
    x1, y1, x2, y2 = w.getBounds()
    groesse = 24 * mm
    d = Drawing(groesse, groesse, transform=[groesse / (x2 - x1), 0, 0, groesse / (y2 - y1), 0, 0])
    d.add(w)
    return d


# ---------------------------------------------------------------- PDF ---

def baue_pdf(pfad: Path) -> Path:
    b = lade_yaml(pfad)
    a = lade_absender(b.get("absender"))
    art = str(b.get("art", "rechnung")).lower()
    if art not in ARTEN:
        sys.exit(f"Unbekannte Art „{art}“. Möglich: {', '.join(ARTEN)}")
    b_datum = datum(b.get("datum"))
    if not b.get("datum") or str(b.get("datum")).lower() == "heute":
        schreibe_feld(pfad, "datum", b_datum.isoformat())
    if str(b.get("leistungsdatum", "")).lower() == "heute":
        b["leistungsdatum"] = b_datum.isoformat()
        schreibe_feld(pfad, "leistungsdatum", b["leistungsdatum"])
    if str(b.get("nummer", "auto")).lower() in ("auto", "", "none"):
        b["nummer"] = naechste_nummer(art, a, b_datum.year)
        schreibe_feld(pfad, "nummer", b["nummer"])
        print(f"Nummer vergeben: {b['nummer']}")
    for warnung in pruefe(b, a, art):
        print(f"⚠ {warnung}")

    b = katalog_aufloesen(b)
    r = berechne(b)
    wae = b.get("waehrung", a.get("waehrung", "EUR"))
    bank = a.get("bank") or {}
    normal, mittel, fett = schriften()
    akzent = colors.HexColor(a.get("akzentfarbe", "#0077C2"))
    tinte = colors.HexColor("#0F1720")
    grau = colors.HexColor("#4A5563")
    linie = colors.HexColor("#E3E8EE")
    zart = colors.HexColor("#E6F5FF")

    st = lambda n, **k: ParagraphStyle(n, fontName=k.pop("f", normal), fontSize=k.pop("s", 9.5),
                                       leading=k.pop("l", 13), textColor=k.pop("c", tinte), **k)
    s_text = st("text")
    s_klein = st("klein", s=8, l=10.5, c=grau)
    s_rechts = st("rechts", alignment=TA_RIGHT)
    s_kopf = st("kopf", f=mittel, s=8, l=10, c=grau)
    s_kopf_r = st("kopfr", f=mittel, s=8, l=10, c=grau, alignment=TA_RIGHT)
    s_pos = st("pos", f=mittel)
    s_titel = st("titel", f=fett, s=20, l=24)
    s_summe = st("summe", f=fett, s=11, l=14, alignment=TA_RIGHT)
    s_summe_l = st("summel", f=fett, s=11, l=14)

    OUT.mkdir(exist_ok=True)
    ziel = OUT / f"{b['nummer']}.pdf"
    titel = b.get("titel") or ARTEN[art]
    if art == "rechnung" and b.get("bezahlt"):
        titel = b.get("titel") or "Rechnung / Quittung"
    W, H = A4
    L, R = 25 * mm, 20 * mm

    fuss_spalten = [
        [a.get("name", ""), a.get("zusatz", ""), a.get("strasse", ""), a.get("plz_ort", "")],
        [a.get("telefon", "") and f"Tel. {a['telefon']}", a.get("email", ""), a.get("web", ""),
         a.get("ust_id") and f"USt-IdNr. {a['ust_id']}",
         a.get("steuernummer") and f"Steuernr. {a['steuernummer']}"],
        [bank.get("bank", ""), bank.get("iban") and f"IBAN {bank['iban']}",
         bank.get("bic") and f"BIC {bank['bic']}", bank.get("kontoinhaber", "")],
    ]

    def rahmen(c, doc, erste: bool):
        c.saveState()
        # Falz- und Lochmarken (DIN 5008)
        c.setStrokeColor(grau)
        c.setLineWidth(0.3)
        for y in (H - 105 * mm, H - 210 * mm):
            c.line(5 * mm, y, 9 * mm, y)
        c.line(5 * mm, H / 2, 11 * mm, H / 2)
        # Kopf
        c.setFillColor(akzent)
        c.rect(0, H - 6 * mm, W, 6 * mm, stroke=0, fill=1)
        logo = a.get("logo")
        if logo and (HIER / logo).exists():
            c.drawImage(str(HIER / logo), W - R - 40 * mm, H - 32 * mm, 40 * mm, 18 * mm,
                        preserveAspectRatio=True, anchor="ne", mask="auto")
        else:
            c.setFillColor(tinte)
            c.setFont(fett, 15)
            c.drawRightString(W - R, H - 20 * mm, a.get("name", ""))
            c.setFont(normal, 8.5)
            c.setFillColor(grau)
            c.drawRightString(W - R, H - 25 * mm, a.get("zusatz", ""))
        if erste:
            # Absenderzeile über dem Anschriftfeld
            c.setFont(normal, 7)
            c.setFillColor(grau)
            zeile = " · ".join(x for x in [a.get("name"), a.get("strasse"), a.get("plz_ort")] if x)
            if c.stringWidth(zeile, normal, 7) > 85 * mm:  # nie in den Infoblock laufen
                c.setFont(normal, 6)
            c.drawString(L, H - 50 * mm, zeile)
            c.setStrokeColor(linie)
            c.line(L, H - 51.2 * mm, L + 85 * mm, H - 51.2 * mm)
            # Anschrift
            e = b.get("empfaenger") or {}
            y = H - 56 * mm
            c.setFillColor(tinte)
            for i, z in enumerate([e.get("firma"), e.get("name"), e.get("zusatz"), e.get("strasse"),
                                   e.get("plz_ort"), e.get("land")]):
                if z:
                    c.setFont(mittel if i == 0 else normal, 10)
                    c.drawString(L, y, str(z))
                    y -= 4.6 * mm
            # Infoblock
            info = [(f"{ARTEN[art]}snr." if art in ("rechnung", "storno", "korrektur", "proforma")
                     else f"{ARTEN[art]}-Nr.", b["nummer"]),
                    ("Datum", de_datum(b_datum))]
            if b.get("leistungsdatum"):
                info.append(("Leistungsdatum" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(b["leistungsdatum"]))
                             or isinstance(b["leistungsdatum"], dt.date) else "Leistungszeitraum",
                             leistung_text(b["leistungsdatum"])))
            if e.get("kundennummer"):
                info.append(("Kundennr.", str(e["kundennummer"])))
            if e.get("ust_id"):
                info.append(("USt-IdNr. Kunde", e["ust_id"]))
            if b.get("bezug"):
                info.append(("Bezug", str(b["bezug"])))
            if art == "angebot":
                gueltig = b.get("gueltig_bis") or (b_datum + dt.timedelta(days=int(a.get("angebot_gueltig_tage", 30)))).isoformat()
                info.append(("Gültig bis", de_datum(gueltig)))
            y = H - 50 * mm
            for k, v in info:
                c.setFont(normal, 8.5)
                c.setFillColor(grau)
                c.drawString(W - R - 70 * mm, y, k)
                c.setFont(mittel, 8.5)
                c.setFillColor(tinte)
                c.drawRightString(W - R, y, v)
                y -= 4.6 * mm
        else:
            c.setFont(normal, 8.5)
            c.setFillColor(grau)
            c.drawString(L, H - 20 * mm, f"{ARTEN[art]} {b['nummer']} vom {de_datum(b_datum)}")
        # Fußzeile
        c.setStrokeColor(linie)
        c.line(L, 27 * mm, W - R, 27 * mm)
        breite = (W - L - R) / 3
        for i, spalte in enumerate(fuss_spalten):
            y = 23 * mm
            for z in [z for z in spalte if z]:
                c.setFont(normal, 7)
                c.setFillColor(grau)
                c.drawString(L + i * breite, y, str(z))
                y -= 3.3 * mm
        c.drawRightString(W - R, 8 * mm, f"Seite {doc.page}")
        c.restoreState()

    doc = BaseDocTemplate(str(ziel), pagesize=A4, title=f"{titel} {b['nummer']}",
                          author=a.get("name", ""), subject=b.get("betreff", ""), creator="rechnung.py")
    # Textbereich direkt unter Anschrift/Infoblock beginnen lassen (spart Platz)
    e0 = b.get("empfaenger") or {}
    n_anschrift = sum(1 for f in ("firma", "name", "zusatz", "strasse", "plz_ort", "land") if e0.get(f))
    n_info = 2 + sum(1 for x in (b.get("leistungsdatum"), e0.get("kundennummer"), e0.get("ust_id"),
                                 b.get("bezug"), art == "angebot") if x)
    oben = max(56 + (n_anschrift - 1) * 4.6, 50 + (n_info - 1) * 4.6) + 12
    f1 = Frame(L, 30 * mm, W - L - R, H - 30 * mm - max(oben, 74) * mm, id="f1", leftPadding=0, rightPadding=0)
    f2 = Frame(L, 32 * mm, W - L - R, H - 32 * mm - 30 * mm, id="f2", leftPadding=0, rightPadding=0)
    doc.addPageTemplates([PageTemplate("erste", [f1], onPage=lambda c, d: rahmen(c, d, True), autoNextPageTemplate="weitere"),
                          PageTemplate("weitere", [f2], onPage=lambda c, d: rahmen(c, d, False))])

    inhalt = [Paragraph(esc(titel), s_titel), Spacer(0, 2 * mm)]
    if b.get("betreff"):
        inhalt += [Paragraph(esc(b["betreff"]), st("betreff", f=mittel, s=10.5)), Spacer(0, 3 * mm)]
    anrede = b.get("einleitung")
    if anrede is None:
        anrede = {"angebot": "Vielen Dank für Ihre Anfrage. Gern biete ich Ihnen folgende Leistungen an:",
                  "storno": f"Hiermit storniere ich die Rechnung {b.get('bezug', '')} vollständig.",
                  "lieferschein": "Folgende Leistungen/Artikel wurden geliefert:",
                  "quittung": "Für meine Leistungen habe ich Ihnen berechnet:",
                  }.get(art, "Für meine Leistungen berechne ich Ihnen:")
    if anrede:
        inhalt += [Paragraph(esc(anrede), s_text), Spacer(0, 4 * mm)]

    # Positionstabelle
    ohne_preise = art == "lieferschein"
    zeige_ust = not r["ohne_ust"] and len({z["satz"] for z in r["zeilen"]}) > 1
    kopf = ["Pos.", "Beschreibung", "Menge"] + ([] if ohne_preise else
            ["Einzelpreis" + (" brutto" if r["brutto_modus"] else ""), *(["USt."] if zeige_ust else []), "Gesamt"])
    daten = [[Paragraph(k, s_kopf_r if i >= 2 else s_kopf) for i, k in enumerate(kopf)]]
    for z in r["zeilen"]:
        beschr = f"<font name='{mittel}'>{esc(z.get('text'))}</font>"
        if z.get("detail"):
            beschr += f"<br/><font size='8' color='#4A5563'>{esc(z['detail'])}</font>"
        reihe = [Paragraph(str(z["nr"]), s_text), Paragraph(beschr, s_text),
                 Paragraph(f"{zahl(z['menge'])} {esc(z.get('einheit', ''))}".strip(), s_rechts)]
        if not ohne_preise:
            reihe += [Paragraph(geld(z["preis"], wae), s_rechts),
                      *([Paragraph(f"{zahl(z['satz'])} %", s_rechts)] if zeige_ust else []),
                      Paragraph(geld(z["betrag"], wae), s_rechts)]
        daten.append(reihe)
    breite = W - L - R
    if ohne_preise:
        spalten = [12 * mm, breite - 42 * mm, 30 * mm]
    else:
        feste = [12 * mm, 22 * mm, 26 * mm] + ([14 * mm] if zeige_ust else []) + [26 * mm]
        spalten = [feste[0], breite - sum(feste)] + feste[1:]
    t = Table(daten, colWidths=spalten, repeatRows=1)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, tinte),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, linie),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
    ]))
    inhalt += [t, Spacer(0, 4 * mm)]

    # Summenblock
    if not ohne_preise:
        sz = []
        mehrere = len(r["gruppen"]) > 1
        for g in r["gruppen"]:
            satz_txt = f" ({zahl(g['satz'])} %)" if mehrere else ""
            if g["abzug"]:
                sz.append([f"Summe Positionen{satz_txt}", geld(g["summe"], wae)])
                sz.append([f"abzgl. {zahl(b['rabatt_prozent'])} % Rabatt{satz_txt}", geld(-g["abzug"], wae)])
            if r["ohne_ust"]:
                continue
            sz.append([f"Nettobetrag{satz_txt}", geld(g["netto"], wae)])
            sz.append([f"zzgl. {zahl(g['satz'])} % USt." if not r["brutto_modus"]
                       else f"enthaltene USt. {zahl(g['satz'])} %", geld(g["steuer"], wae)])
        label = "Gesamtbetrag" if r["ohne_ust"] else "Rechnungsbetrag" if art in STEUERBELEGE else "Gesamtbetrag brutto"
        if art == "angebot":
            label = "Angebotssumme" + ("" if r["ohne_ust"] else " brutto")
        reihen = [[Paragraph(k, s_rechts), Paragraph(v, s_rechts)] for k, v in sz]
        reihen.append([Paragraph(label, s_summe), Paragraph(geld(r["brutto"], wae), s_summe)])
        ts = Table(reihen, colWidths=[breite - 36 * mm, 36 * mm])
        ts.setStyle(TableStyle([
            ("LINEABOVE", (0, -1), (-1, -1), 0.8, tinte),
            ("BACKGROUND", (0, -1), (-1, -1), zart),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, -1), (-1, -1), 5), ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
            ("RIGHTPADDING", (-1, 0), (-1, -1), 2),
        ]))
        inhalt += [KeepTogether([ts]), Spacer(0, 6 * mm)]

    # Hinweise: Steuerfall, Zahlung, Schluss
    hinweise = []
    if STEUERFAELLE.get(b.get("steuerfall", "normal")):
        hinweise.append(f"<font name='{mittel}'>{STEUERFAELLE[b['steuerfall']]}</font>")
    bezahlt = b.get("bezahlt")
    qr = None
    if art == "quittung" or bezahlt:
        bz = bezahlt if isinstance(bezahlt, dict) else {}
        wann = de_datum(bz.get("datum")) if bz.get("datum") else de_datum(b_datum)
        wie = f" per {esc(bz['art'])}" if bz.get("art") else ""
        hinweise.append(f"<font name='{fett}' color='{akzent.hexval().replace('0x', '#')}'>"
                        f"Betrag dankend erhalten am {wann}{wie}.</font>")
    elif art in ("rechnung", "korrektur", "proforma") and r["brutto"] > 0:
        tage = int(b.get("zahlungsziel_tage", a.get("zahlungsziel_tage", 14)))
        faellig = b_datum + dt.timedelta(days=tage)
        txt = (f"Bitte überweisen Sie den Betrag von <font name='{mittel}'>{geld(r['brutto'], wae)}</font> "
               f"bis zum <font name='{mittel}'>{de_datum(faellig)}</font> unter Angabe der "
               f"Rechnungsnummer <font name='{mittel}'>{esc(b['nummer'])}</font>")
        if bank.get("iban"):
            txt += f" auf das Konto IBAN {esc(bank['iban'])}"
            if bank.get("bic"):
                txt += f", BIC {esc(bank['bic'])}"
        hinweise.append(txt + ".")
        if b.get("zahlungslink"):
            hinweise.append(f"Online bezahlen: <link href='{esc(b['zahlungslink'])}' color='#0077C2'>"
                            f"{esc(b['zahlungslink'])}</link>")
        if wae == "EUR" and b.get("girocode", True):
            qr = girocode(bank, r["brutto"], f"{b['nummer']}", a.get("name", ""))
    elif art == "storno":
        hinweise.append("Ein bereits gezahlter Betrag wird Ihnen erstattet.")
    if a.get("aufbewahrung_hinweis") and art in STEUERBELEGE and not b.get("empfaenger", {}).get("firma"):
        hinweise.append(esc(a["aufbewahrung_hinweis"]))
    if b.get("hinweis"):
        hinweise.append(esc(b["hinweis"]))
    schluss = b.get("schluss", a.get("schluss", "Vielen Dank für Ihr Vertrauen!"))

    block = []
    for h in hinweise:
        block += [Paragraph(h, s_text), Spacer(0, 2 * mm)]
    if schluss:
        block += [Spacer(0, 2 * mm), Paragraph(esc(schluss), s_text)]
        if a.get("gruss"):
            block += [Spacer(0, 2 * mm), Paragraph(esc(a["gruss"]), s_text)]
    if qr:
        # QR-Code rechts neben Zahlungshinweis und Gruß – spart eine Seite
        qr_tab = Table([[block, [qr, Paragraph("GiroCode: mit der<br/>Banking-App scannen", s_klein)]]],
                       colWidths=[breite - 32 * mm, 32 * mm])
        qr_tab.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        inhalt.append(KeepTogether([qr_tab]))
    else:
        inhalt += block
    doc.build(inhalt)
    print(f"✓ {ziel.relative_to(HIER.parent)}  ({geld(r['brutto'], wae)})")
    return ziel


# ---------------------------------------------------------------- Befehle ---

def dateiname(nummer_oder_art: str, kunde: str = "") -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", kunde.lower()).strip("-")
    basis = f"{dt.date.today().isoformat()}-{nummer_oder_art}" + (f"-{slug}" if slug else "")
    p = BELEGE / f"{basis}.yaml"
    i = 2
    while p.exists():
        p = BELEGE / f"{basis}-{i}.yaml"
        i += 1
    return p


def cmd_neu(args):
    vorlage = VORLAGEN / f"{args.vorlage or args.art}.yaml"
    if not vorlage.exists():
        vorlage = VORLAGEN / "rechnung.yaml"
    BELEGE.mkdir(exist_ok=True)
    ziel = dateiname(f"{args.art}-{args.vorlage}" if args.vorlage else args.art, args.kunde or "")
    text = vorlage.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^art:.*$", f"art: {args.art}", text)
    text = re.sub(r"(?m)^datum:.*$", f"datum: {dt.date.today().isoformat()}", text)
    ziel.write_text(text, encoding="utf-8")
    print(f"Angelegt: {ziel.relative_to(HIER.parent)}\nAusfüllen, dann: python3 rechnungen/rechnung.py bauen {ziel.relative_to(HIER.parent)}")


def cmd_artikel(args):
    kat = lade_katalog(args.katalog)
    print(f"{kat.get('katalog', args.katalog)} – Preise {kat.get('preise', 'netto')}"
          + (f", Stand {kat['stand']}" if kat.get("stand") else "") + "\n")
    print(f"  {'Art.-Nr.':<10} {'Produkt':<52} {'Preis':>10}  USt.   Schlüssel")
    for k, e in (kat.get("artikel") or {}).items():
        preis = "– fehlt –" if e.get("preis") is None else geld(dec(e["preis"]))
        print(f"  {str(e.get('artikelnr', '')):<10} {e.get('text', '')[:52]:<52} {preis:>10}  "
              f"{zahl(e.get('ust', kat.get('standard_ust', 19))):>2} %   {k}")
    if kat.get("aliase"):
        print("\nKurznamen: " + ", ".join(f"{a} → {z}" for a, z in kat["aliase"].items()))


def cmd_bauen(args):
    for p in args.dateien:
        baue_pdf(Path(p))


def kopiere_beleg(quelle: Path, art: str, extra: dict, minus: bool = False) -> Path:
    b = katalog_aufloesen(lade_yaml(quelle)) if minus else lade_yaml(quelle)
    b.update({"art": art, "nummer": "auto", "datum": dt.date.today().isoformat(), **extra})
    b.pop("bezahlt", None)
    b.pop("gueltig_bis", None)
    if art != "angebot":
        for feld in ("einleitung", "hinweis", "schluss"):
            b.pop(feld, None)
    if minus:
        for pos in b.get("positionen") or []:
            pos["preis"] = -float(dec(pos.get("preis")))
    kunde = (b.get("empfaenger") or {}).get("firma") or (b.get("empfaenger") or {}).get("name") or ""
    ziel = dateiname(art, kunde)
    ziel.write_text(f"# Erzeugt aus {quelle.name}\n" + yaml.safe_dump(b, allow_unicode=True, sort_keys=False),
                    encoding="utf-8")
    print(f"Angelegt: {ziel.relative_to(HIER.parent)}")
    return ziel


def cmd_umwandeln(args):
    q = Path(args.datei)
    b = lade_yaml(q)
    ziel = kopiere_beleg(q, args.ziel, {"bezug": f"Angebot {b.get('nummer')}"} if b.get("art") == "angebot" else {})
    print("Leistungsdatum prüfen/eintragen, dann bauen.")
    if not args.nur_yaml:
        baue_pdf(ziel)


def cmd_storno(args):
    q = Path(args.datei)
    b = lade_yaml(q)
    if str(b.get("nummer", "auto")) == "auto":
        sys.exit("Die Rechnung hat noch keine Nummer – erst bauen.")
    ziel = kopiere_beleg(q, "storno", {"bezug": b["nummer"], "leistungsdatum": b.get("leistungsdatum")}, minus=True)
    schreibe_feld(q, "storniert_durch", lade_yaml(ziel).get("nummer", "auto"))
    p = baue_pdf(ziel)
    schreibe_feld(q, "storniert_durch", lade_yaml(ziel)["nummer"])
    return p


def cmd_bezahlt(args):
    q = Path(args.datei)
    text = q.read_text(encoding="utf-8")
    text = re.sub(r"(?ms)^bezahlt:.*?(?=^\S|\Z)", "", text)
    wann = args.datum or dt.date.today().isoformat()
    text = text.rstrip() + f"\nbezahlt:\n  datum: {wann}\n" + (f"  art: {args.art}\n" if args.art else "")
    q.write_text(text, encoding="utf-8")
    print(f"Als bezahlt markiert ({de_datum(wann)}).")
    if args.quittung:
        baue_pdf(q)


def ausgangsbuch(jahr: int | None):
    zeilen = []
    for p, b in alle_belege():
        art = str(b.get("art", "rechnung"))
        if art not in STEUERBELEGE or str(b.get("nummer", "auto")) == "auto":
            continue
        d = datum(b.get("datum"))
        if jahr and d.year != jahr:
            continue
        r = berechne(b)
        e = b.get("empfaenger") or {}
        bz = b.get("bezahlt") if isinstance(b.get("bezahlt"), dict) else {}
        tage = int(b.get("zahlungsziel_tage", 14))
        status = ("bezahlt" if (b.get("bezahlt") or art == "quittung") else
                  "storniert" if b.get("storniert_durch") else
                  "Storno" if art == "storno" else
                  "überfällig" if dt.date.today() > d + dt.timedelta(days=tage) else "offen")
        zeilen.append({
            "Nummer": b["nummer"], "Art": ARTEN[art], "Datum": d.isoformat(),
            "Kunde": e.get("firma") or e.get("name", ""),
            "Netto": f"{r['netto']:.2f}".replace(".", ","), "USt": f"{r['steuer']:.2f}".replace(".", ","),
            "Brutto": f"{r['brutto']:.2f}".replace(".", ","),
            **{f"USt {zahl(g['satz'])} %": f"{g['steuer']:.2f}".replace(".", ",") for g in r["gruppen"]},
            "Status": status, "Bezahlt am": bz.get("datum", "") or "", "Bezug": b.get("bezug", "") or "",
            "Datei": p.name, "_brutto": r["brutto"],
        })
    zeilen.sort(key=lambda z: (z["Datum"], z["Nummer"]))
    return zeilen


def cmd_liste(args):
    zeilen = ausgangsbuch(args.jahr)
    if not zeilen:
        print("Noch keine gebauten Rechnungen in rechnungen/belege/.")
        return None
    felder = []
    for z in zeilen:
        felder += [k for k in z if k not in felder and not k.startswith("_")]
    OUT.mkdir(exist_ok=True)
    csv_pfad = OUT / f"ausgangsbuch{'-' + str(args.jahr) if args.jahr else ''}.csv"
    with open(csv_pfad, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, felder, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(zeilen)
    for z in zeilen:
        print(f"{z['Nummer']:<16} {z['Datum']}  {z['Kunde'][:26]:<26} {geld(z['_brutto']):>14}  {z['Status']}")
    offen = sum((z["_brutto"] for z in zeilen if z["Status"] in ("offen", "überfällig")), D0)
    summe = sum((z["_brutto"] for z in zeilen), D0)
    print(f"\nUmsatz brutto: {geld(summe)} · offen: {geld(offen)}\nCSV: {csv_pfad.relative_to(HIER.parent)}")
    return csv_pfad


def cmd_archiv(args):
    csv_pfad = cmd_liste(args)
    if not csv_pfad:
        return
    ziel = OUT / f"rechnungen-{args.jahr or 'alle'}.zip"
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(csv_pfad, csv_pfad.name)
        for zeile in ausgangsbuch(args.jahr):
            pdf = OUT / f"{zeile['Nummer']}.pdf"
            if not pdf.exists():
                baue_pdf(BELEGE / zeile["Datei"])
            z.write(pdf, f"pdf/{pdf.name}")
    print(f"✓ Archiv: {ziel.relative_to(HIER.parent)}")


def main():
    ap = argparse.ArgumentParser(description="Rechnungen und Angebote als PDF")
    sub = ap.add_subparsers(dest="befehl", required=True)
    p = sub.add_parser("neu", help="neuen Beleg aus Vorlage anlegen")
    p.add_argument("art", choices=list(ARTEN))
    p.add_argument("--kunde", help="Kundenname für den Dateinamen")
    p.add_argument("--vorlage", help="andere Vorlage aus vorlagen/, z. B. fitline")
    p.set_defaults(f=cmd_neu)
    p = sub.add_parser("artikel", help="Artikel eines Katalogs anzeigen")
    p.add_argument("katalog", nargs="?", default="fitline")
    p.set_defaults(f=cmd_artikel)
    p = sub.add_parser("bauen", help="PDF erzeugen")
    p.add_argument("dateien", nargs="+")
    p.set_defaults(f=cmd_bauen)
    p = sub.add_parser("umwandeln", help="Angebot in Rechnung (oder andere Art) umwandeln")
    p.add_argument("datei")
    p.add_argument("--ziel", default="rechnung", choices=list(ARTEN))
    p.add_argument("--nur-yaml", action="store_true", help="nur YAML anlegen, nicht bauen")
    p.set_defaults(f=cmd_umwandeln)
    p = sub.add_parser("storno", help="Stornorechnung erstellen")
    p.add_argument("datei")
    p.set_defaults(f=cmd_storno)
    p = sub.add_parser("bezahlt", help="als bezahlt markieren")
    p.add_argument("datei")
    p.add_argument("--datum")
    p.add_argument("--art", help="z. B. Überweisung, bar, PayPal")
    p.add_argument("--quittung", action="store_true", help="PDF mit Zahlungsvermerk neu bauen")
    p.set_defaults(f=cmd_bezahlt)
    for name, f in (("liste", cmd_liste), ("archiv", cmd_archiv)):
        p = sub.add_parser(name)
        p.add_argument("--jahr", type=int)
        p.set_defaults(f=f)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
