#!/usr/bin/env python3
"""Baut Band 1 aus buch/kapitel/*.md zu einem druckfertigen .docx.

    python3 buch/build/build_docx.py

Danach in ein PDF wandeln:

    soffice --headless --convert-to pdf --outdir buch/out buch/out/<slug>.docx

Unterstützte Markdown-Teilmenge: Überschriften H1–H3, Absätze, Aufzählungen,
nummerierte Listen, Tabellen (GFM-Pipe), **fett**, *kursiv*, Blockzitate als
Hinweiskästen, Trennlinien. Dazu drei eigene Marker in einer eigenen Zeile:

    {{INHALTSVERZEICHNIS}}   Word-TOC-Feld
    {{SEITENUMBRUCH}}        harter Seitenumbruch
    {{LEERZEILE}}            vertikaler Abstand
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Mm, Pt
from markdown_it import MarkdownIt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stile  # noqa: E402

WURZEL = Path(__file__).resolve().parents[2]
BUCH = WURZEL / "buch"


# --- PDF-Erzeugung -----------------------------------------------------------
def pdf_erzeugen(docx_pfad):
    """Wandelt .docx nach .pdf via LibreOffice.

    Ein eigenes Benutzerprofil in einem Temporärverzeichnis vermeidet
    Sperrdateien, wenn mehrere Läufe kurz hintereinander erfolgen.
    """
    docx_pfad = Path(docx_pfad)
    pdf_pfad = docx_pfad.with_suffix(".pdf")
    pdf_pfad.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="lo_") as profil:
        ergebnis = subprocess.run(
            ["soffice", "--headless",
             f"-env:UserInstallation=file://{profil}",
             "--convert-to", "pdf",
             "--outdir", str(docx_pfad.parent), str(docx_pfad)],
            capture_output=True, text=True,
        )
    if not pdf_pfad.exists():
        raise SystemExit(
            "LibreOffice konnte kein PDF erzeugen.\n"
            f"stdout: {ergebnis.stdout}\nstderr: {ergebnis.stderr}\n"
            "Prüfe, ob das Paket libreoffice-writer installiert ist "
            "(apt-get update && apt-get install -y libreoffice-writer)."
        )
    return pdf_pfad


# --- Kapiteldateien ----------------------------------------------------------
def kapitel_laden(verzeichnis):
    """Liest alle .md-Dateien in Dateinamen-Reihenfolge samt Front Matter."""
    kapitel = []
    for pfad in sorted(verzeichnis.glob("*.md")):
        roh = pfad.read_text(encoding="utf-8")
        kopf, rumpf = _front_matter_trennen(roh)
        kopf.setdefault("typ", "kapitel")
        kopf.setdefault("kopfzeile", kopf.get("titel", pfad.stem))
        kapitel.append({"pfad": pfad, "meta": kopf, "text": rumpf})
    if not kapitel:
        raise SystemExit(f"Keine Kapitel in {verzeichnis} gefunden.")
    return kapitel


def _front_matter_trennen(roh):
    if not roh.startswith("---"):
        return {}, roh
    teile = roh.split("---", 2)
    if len(teile) < 3:
        return {}, roh
    return yaml.safe_load(teile[1]) or {}, teile[2].lstrip("\n")


# --- Markdown → docx ---------------------------------------------------------
class Renderer:
    """Übersetzt den Token-Strom von markdown-it in Word-Absätze."""

    UEBERSCHRIFT = {"h1": "Kapitel", "h2": "Abschnitt", "h3": "Unterabschnitt"}

    # Abweichende Zuordnung für die Titelseite: H1 wird zum Buchtitel,
    # H2 zum Untertitel, H3 zur Autorenzeile — alles zentriert.
    UEBERSCHRIFT_TITELSEITE = {
        "h1": "BuchTitel", "h2": "BuchUntertitel", "h3": "BuchAutor",
    }
    # Teil-Trennseiten: H1 = "Teil III", H2 = Titel des Teils.
    UEBERSCHRIFT_TEIL = {
        "h1": "Teilnummer", "h2": "Teiltitel", "h3": "Unterabschnitt",
    }
    LAYOUTS = {"titelseite": UEBERSCHRIFT_TITELSEITE, "teil": UEBERSCHRIFT_TEIL}

    def __init__(self, doc, textbreite_mm, toc_daten=None):
        self.doc = doc
        self.textbreite_mm = textbreite_mm
        self.toc_daten = toc_daten
        self.ueberschrift_karte = self.UEBERSCHRIFT
        self.md = MarkdownIt("commonmark").enable("table").enable("strikethrough")

    def rendern(self, markdown_text, ueberschriften=None):
        self.ueberschrift_karte = ueberschriften or self.UEBERSCHRIFT
        tokens = self.md.parse(self._marker_isolieren(markdown_text))
        self._block(tokens, 0, len(tokens))

    @staticmethod
    def _marker_isolieren(text):
        """Umgibt jede Markerzeile mit Leerzeilen.

        Ohne das verschmelzen zwei untereinanderstehende {{LEERZEILE}} zu einem
        einzigen Markdown-Absatz und würden wörtlich gedruckt.
        """
        return re.sub(r"(?m)^([ \t]*\{\{[A-ZÄÖÜ]+\}\}[ \t]*)$", r"\n\1\n", text)

    # -- Blockebene --
    def _block(self, tokens, start, ende, *, listenstil=None, zaehler=None):
        i = start
        while i < ende:
            t = tokens[i]
            typ = t.type

            if typ == "heading_open":
                stilname = self.ueberschrift_karte.get(t.tag, "Unterabschnitt")
                absatz = self.doc.add_paragraph(style=stilname)
                self._inline(absatz, tokens[i + 1])
                i += 3
                continue

            if typ == "paragraph_open":
                inhalt = tokens[i + 1]
                marker = self._marker(inhalt.content)
                if marker:
                    marker()
                else:
                    stilname = listenstil or "Fliesstext"
                    absatz = self.doc.add_paragraph(style=stilname)
                    if listenstil == "Punkt":
                        absatz.add_run("•  ")
                    elif listenstil == "Nummer" and zaehler is not None:
                        absatz.add_run(f"{zaehler[0]}.  ")
                        zaehler[0] += 1
                    self._inline(absatz, inhalt)
                i += 3
                continue

            if typ in ("bullet_list_open", "ordered_list_open"):
                schluss = self._passendes_ende(tokens, i)
                stilname = "Punkt" if typ == "bullet_list_open" else "Nummer"
                zaehler_neu = [int(t.attrGet("start") or 1)]
                self._block(tokens, i + 1, schluss,
                            listenstil=stilname, zaehler=zaehler_neu)
                i = schluss + 1
                continue

            if typ == "list_item_open":
                schluss = self._passendes_ende(tokens, i)
                self._block(tokens, i + 1, schluss,
                            listenstil=listenstil, zaehler=zaehler)
                i = schluss + 1
                continue

            if typ == "blockquote_open":
                schluss = self._passendes_ende(tokens, i)
                self._kasten(tokens, i + 1, schluss)
                i = schluss + 1
                continue

            if typ == "table_open":
                schluss = self._passendes_ende(tokens, i)
                self._tabelle(tokens, i, schluss)
                i = schluss + 1
                continue

            if typ == "hr":
                self._trennlinie()
                i += 1
                continue

            if typ in ("fence", "code_block"):
                absatz = self.doc.add_paragraph(style="Klein")
                absatz.add_run(t.content.rstrip())
                i += 1
                continue

            i += 1

    def _passendes_ende(self, tokens, start):
        """Index des schließenden Tokens zum Öffner an `start`."""
        tiefe = 0
        oeffner = tokens[start].type
        schliesser = oeffner.replace("_open", "_close")
        for i in range(start, len(tokens)):
            if tokens[i].type == oeffner:
                tiefe += 1
            elif tokens[i].type == schliesser:
                tiefe -= 1
                if tiefe == 0:
                    return i
        return len(tokens) - 1

    # -- Marker --
    def _marker(self, text):
        treffer = re.fullmatch(r"\{\{([A-ZÄÖÜ]+)\}\}", text.strip())
        if not treffer:
            return None
        name = treffer.group(1)
        if name == "INHALTSVERZEICHNIS":
            return self._inhaltsverzeichnis
        if name == "SEITENUMBRUCH":
            return lambda: stile.seitenumbruch(self.doc)
        if name == "LEERZEILE":
            return lambda: self.doc.add_paragraph(style="Fliesstext")
        return None

    def _inhaltsverzeichnis(self):
        """Statisches Verzeichnis aus den Seitenzahlen des ersten Durchlaufs.

        Word-TOC-Felder werden von LibreOffice beim PDF-Export nicht
        aufgelöst — dort stünde nur ein Platzhalter. Deshalb wird das
        Verzeichnis selbst gesetzt.
        """
        if not self.toc_daten:
            # Erster Durchlauf: Platz reservieren, damit die Titelei schon
            # ungefähr die spätere Länge hat.
            self.doc.add_paragraph(style="Fliesstext")
            return
        for eintrag in self.toc_daten:
            ist_teil = eintrag["typ"] == "teil"
            absatz = self.doc.add_paragraph(
                style="InhaltTeil" if ist_teil else "InhaltKapitel")
            stile.tabulator_rechts(absatz, self.textbreite_mm)
            beschriftung = eintrag["titel"]
            if eintrag.get("nummer") and not ist_teil:
                beschriftung = f"{eintrag['nummer']}.  {beschriftung}"
            elif not ist_teil:
                absatz.paragraph_format.left_indent = Mm(4)
            absatz.add_run(beschriftung)
            absatz.add_run("\t")
            absatz.add_run(str(eintrag["seite"]))

    # -- Hinweiskasten --
    def _kasten(self, tokens, start, ende):
        """Blockzitat wird zum getönten Kasten. Endet die erste Zeile auf einen
        Doppelpunkt, wird sie als Kastentitel gesetzt."""
        absaetze = []
        i = start
        while i < ende:
            if tokens[i].type == "paragraph_open":
                absaetze.append(tokens[i + 1])
                i += 3
            else:
                i += 1

        for nummer, inhalt in enumerate(absaetze):
            erster = nummer == 0
            letzter = nummer == len(absaetze) - 1
            ist_titel = erster and inhalt.content.rstrip().endswith(":")
            absatz = self.doc.add_paragraph(
                style="KastenTitel" if ist_titel else "KastenText")
            self._inline(absatz, inhalt)
            stile.schattierung(absatz, stile.FARBEN["kasten"])
            absatz.paragraph_format.left_indent = Mm(4)
            absatz.paragraph_format.right_indent = Mm(4)
            if erster:
                absatz.paragraph_format.space_before = Pt(8)
            if letzter:
                absatz.paragraph_format.space_after = Pt(10)
            kanten = []
            if erster:
                kanten.append("top")
            if letzter:
                kanten.append("bottom")
            kanten += ["left", "right"]
            stile.rahmen(absatz, "D3E3CC", staerke=6, seiten=tuple(kanten))

    # -- Tabelle --
    def _tabelle(self, tokens, start, ende):
        zeilen, kopfzeilen = [], 0
        i = start
        im_kopf = False
        while i <= ende:
            typ = tokens[i].type
            if typ == "thead_open":
                im_kopf = True
            elif typ == "thead_close":
                im_kopf = False
            elif typ == "tr_open":
                schluss = self._passendes_ende(tokens, i)
                zellen = [tokens[j + 1] for j in range(i, schluss)
                          if tokens[j].type in ("th_open", "td_open")]
                zeilen.append(zellen)
                if im_kopf:
                    kopfzeilen += 1
                i = schluss
            i += 1

        if not zeilen:
            return

        spalten = max(len(z) for z in zeilen)
        tabelle = self.doc.add_table(rows=len(zeilen), cols=spalten)
        tabelle.autofit = False
        stile.tabellenraender(tabelle)

        breite = Mm(self.textbreite_mm / spalten)
        for nummer, zellen in enumerate(zeilen):
            zeile = tabelle.rows[nummer]
            stile.zeile_zusammenhalten(zeile)
            ist_kopf = nummer < kopfzeilen
            if ist_kopf:
                stile.kopfzeile_wiederholen(zeile)
            for spalte in range(spalten):
                zelle = zeile.cells[spalte]
                zelle.width = breite
                absatz = zelle.paragraphs[0]
                absatz.style = self.doc.styles[
                    "TabellenKopf" if ist_kopf else "TabellenZelle"]
                if spalte < len(zellen):
                    self._inline(absatz, zellen[spalte])
                if ist_kopf:
                    stile.schattierung(zelle, "EDF2E9")

        nachlauf = self.doc.add_paragraph(style="FliesstextEng")
        nachlauf.paragraph_format.space_after = Pt(8)

    def _trennlinie(self):
        absatz = self.doc.add_paragraph(style="FliesstextEng")
        absatz.alignment = WD_ALIGN_PARAGRAPH.CENTER
        lauf = absatz.add_run("•  •  •")
        lauf.font.color.rgb = stile.FARBEN["blatt_hell"]
        absatz.paragraph_format.space_before = Pt(6)
        absatz.paragraph_format.space_after = Pt(10)

    # -- Inline --
    def _inline(self, absatz, token):
        if token is None or token.type != "inline":
            return
        fett = kursiv = False
        for kind in token.children or []:
            if kind.type == "strong_open":
                fett = True
            elif kind.type == "strong_close":
                fett = False
            elif kind.type == "em_open":
                kursiv = True
            elif kind.type == "em_close":
                kursiv = False
            elif kind.type in ("text", "code_inline"):
                lauf = absatz.add_run(kind.content)
                # Nur setzen, wenn die Auszeichnung wirklich gilt. Ein
                # explizites False schriebe <w:b w:val="0"/> auf den Lauf und
                # überstimmte damit fette Absatzformate wie "Kapitel".
                if fett:
                    lauf.bold = True
                if kursiv:
                    lauf.italic = True
            elif kind.type == "softbreak":
                absatz.add_run(" ")
            elif kind.type == "hardbreak":
                absatz.add_run("\n")


# --- Zusammenbau -------------------------------------------------------------
def _layout(kap):
    """Überschriften-Zuordnung für ein Kapitel.

    Steuerbar über `layout:` im Front Matter; Teil-Trennseiten bekommen ihre
    Zuordnung automatisch über `typ: teil`.
    """
    name = kap["meta"].get("layout")
    if not name and kap["meta"]["typ"] == "teil":
        name = "teil"
    return Renderer.LAYOUTS.get(name)


def bauen(cfg, kapitel, ziel, toc_daten=None):
    sf = cfg["seitenformat"]
    doc = stile.dokument_anlegen(sf)
    textbreite = sf["breite_mm"] - sf["rand_innen_mm"] - sf["rand_aussen_mm"]
    renderer = Renderer(doc, textbreite, toc_daten)

    titelei = [k for k in kapitel if k["meta"]["typ"] == "titelei"]
    rumpf = [k for k in kapitel if k["meta"]["typ"] != "titelei"]

    # Titelei: römische Seitenzahlen, keine Kopfzeile.
    erste = doc.sections[0]
    stile.seitenzahlen_format(erste, "lowerRoman", neustart_bei=1)
    for nummer, kap in enumerate(titelei):
        if nummer:
            stile.seitenumbruch(doc)
        renderer.rendern(kap["text"], _layout(kap))

    # Rumpf: je Kapitel ein eigener Abschnitt, damit die Kopfzeile den
    # Kapitelnamen tragen kann. Seitenzählung startet neu bei 1.
    #
    # Teilüberschriften bekommen keinen eigenen Abschnitt und damit keine
    # eigene Seite. Sie werden dem ersten Kapitel ihres Teils vorangestellt.
    # Auf 60 Seiten Umfang kosteten sechs Trennseiten ein Zehntel des Buches,
    # ohne eine Zeile Inhalt zu tragen; die Gliederung bleibt über die
    # Überschrift und das Inhaltsverzeichnis erhalten.
    offener_teil = None
    abschnitt_nr = 0
    for kap in rumpf:
        if kap["meta"]["typ"] == "teil":
            offener_teil = kap
            continue

        section = stile.neuer_abschnitt(doc, sf)
        if abschnitt_nr == 0:
            stile.seitenzahlen_format(section, "decimal", neustart_bei=1)
        else:
            stile.seitenzahlen_format(section, "decimal")
        abschnitt_nr += 1
        stile.kopf_und_fusszeile(
            doc, section,
            links_text=cfg["titel"],
            rechts_text=kap["meta"]["kopfzeile"],
        )
        if offener_teil is not None:
            renderer.rendern(offener_teil["text"], _layout(offener_teil))
            offener_teil = None
        renderer.rendern(kap["text"], _layout(kap))

    ziel.parent.mkdir(parents=True, exist_ok=True)
    doc.save(ziel)
    return ziel


def seitenzahlen_ermitteln(pdf_pfad, kapitel):
    """Ordnet jedem Rumpfkapitel seine gedruckte Seitenzahl zu.

    Die Titelei zählt in römischen Ziffern, der Rumpf startet neu bei 1.
    Gesucht wird die PDF-Seite, auf der die Kapitelüberschrift als erste
    Textzeile steht; die gedruckte Zahl ergibt sich aus dem Abstand zur
    ersten Rumpfseite.
    """
    from pypdf import PdfReader

    seiten = [(s.extract_text() or "").strip().splitlines()
              for s in PdfReader(str(pdf_pfad)).pages]
    rumpf = [k for k in kapitel if k["meta"]["typ"] != "titelei"]

    def schluessel(text):
        """Nur Buchstaben und Ziffern, klein geschrieben.

        Der Vergleich muss über Zeilenumbrüche, Gedankenstriche und doppelte
        Leerzeichen hinweg funktionieren: Im PDF steht die Teilüberschrift als
        zwei getrennte Zeilen („Teil I" und der Name), in der YAML-Angabe
        dagegen als eine Zeile mit Gedankenstrich dazwischen.
        """
        return "".join(z for z in text.lower() if z.isalnum())

    treffer, suche_ab = [], 0
    nach_teil = False
    for kap in rumpf:
        titel = kap["meta"].get("titel") or kap["meta"]["kopfzeile"]
        gesucht = schluessel(titel)
        # Die ersten Zeilen einer Seite, nicht nur die allererste: Ganz oben
        # steht die Kolumnentitelzeile. Folgt das Kapitel direkt auf eine
        # Teilüberschrift, stehen davor zusätzlich deren zwei Zeilen und der
        # einleitende Absatz des Teils — dann muss das Fenster größer sein.
        fenster = 16 if nach_teil else 6
        gefunden = None
        for index in range(suche_ab, len(seiten)):
            if gesucht in schluessel(" ".join(seiten[index][:fenster])):
                gefunden = index
                break
        if gefunden is None:
            # Kapitel nicht auffindbar (z. B. Überschrift umgebrochen):
            # lieber keine Zahl als eine falsche.
            treffer.append((kap, None))
            continue
        treffer.append((kap, gefunden))
        # Teilüberschrift und erstes Kapitel des Teils teilen sich eine Seite,
        # deshalb hier nicht weiterspringen.
        nach_teil = kap["meta"]["typ"] == "teil"
        suche_ab = gefunden if nach_teil else gefunden + 1

    erste_rumpfseite = next((i for _, i in treffer if i is not None), 0)
    eintraege = []
    for kap, index in treffer:
        if index is None:
            continue
        eintraege.append({
            "typ": kap["meta"]["typ"],
            "titel": kap["meta"].get("titel") or kap["meta"]["kopfzeile"],
            "nummer": kap["meta"].get("nummer"),
            "seite": index - erste_rumpfseite + 1,
        })
    return eintraege


def main():
    cfg = yaml.safe_load((BUCH / "buch.yaml").read_text(encoding="utf-8"))
    kapitel = kapitel_laden(BUCH / "kapitel")
    ziel = BUCH / "out" / f"{cfg['slug']}.docx"

    # Durchlauf 1: ohne Verzeichnis, nur um die Seitenzahlen zu erfahren.
    bauen(cfg, kapitel, ziel)
    pdf = pdf_erzeugen(ziel)
    toc = seitenzahlen_ermitteln(pdf, kapitel)

    # Durchlauf 2: mit fertigem Verzeichnis. Weil die Titelei römisch und der
    # Rumpf dezimal ab 1 zählt, verschiebt das längere Verzeichnis die
    # Rumpfseitenzahlen nicht — ein zweiter Durchlauf genügt.
    bauen(cfg, kapitel, ziel, toc_daten=toc)
    pdf = pdf_erzeugen(ziel)

    from pypdf import PdfReader
    seiten = len(PdfReader(str(pdf)).pages)
    print(f"{len(kapitel)} Kapitel, {len(toc)} Verzeichniseinträge, "
          f"{seiten} Seiten")
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {pdf.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
