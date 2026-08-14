#!/usr/bin/env python3
"""Baut die Kindle-Ausgaben als EPUB 3.

    python3 buch/build/build_epub.py

Zwei Bände, zwei Bauarten — und das ist kein Schönheitsfehler, sondern folgt
daraus, wozu die Bände da sind:

**Band 1 — fließender Text.** Ein Lesebuch gehört auf dem Kindle reflowable
gesetzt: Der Leser stellt Schriftgröße und Rand selbst ein, der Text läuft
neu um. Feste Seitenzahlen, Kopfzeilen und ein Inhaltsverzeichnis mit
Seitenangaben gibt es hier nicht — an ihre Stelle tritt die Navigation, die
der Reader selbst anzeigt. Gebaut wird direkt aus buch/kapitel/*.md, nicht
aus dem Druck-PDF.

**Band 2 — feste Seiten.** Das Workbook besteht aus Tageskarten und
Schreiblinien. Umflossener Text zerstört diese Seiten: Aus einer Karte würde
eine Liste von Beschriftungen ohne die Felder, zu denen sie gehören. Deshalb
als pre-paginated EPUB — jede Druckseite wird als Bild eingelegt, das Layout
bleibt exakt erhalten.

Was das für Band 2 bedeutet, offen gesagt: Ein Heft zum Ausfüllen ist als
E-Book ein Kompromiss. Man kann darin nicht schreiben. Die Kindle-Ausgabe ist
sinnvoll als Leseprobe und als Nachschlagefassung neben dem gedruckten Heft —
nicht als Ersatz dafür.

Erzeugt wird EPUB, nicht MOBI oder KPF: KDP nimmt EPUB für Kindle-Bücher
entgegen und wandelt selbst. Ein Konverter (kindlegen, Kindle Previewer)
steht in dieser Bauumgebung nicht zur Verfügung und wäre auch nicht nötig.
"""

import html
import re
import sys
import zipfile
from datetime import date
from pathlib import Path

import yaml
from markdown_it import MarkdownIt

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_docx import kapitel_laden  # noqa: E402

# Kennung des Buchs im EPUB. Keine ISBN: Für Kindle-Bücher vergibt Amazon eine
# ASIN, eine ISBN ist weder nötig noch erwünscht. Die Kennung muss nur
# innerhalb des Katalogs eindeutig und über Auflagen hinweg stabil sein.
KENNUNG = "urn:uuid:8f2c1a90-{band}-4e21-9a77-mvd{jahr}"


# --- EPUB-Gerüst -------------------------------------------------------------
def epub_schreiben(ziel, dateien, *, unkomprimiert=("mimetype",)):
    """Schreibt das ZIP-Archiv.

    Die Datei `mimetype` muss die erste im Archiv sein und darf nicht
    komprimiert werden — so steht es in der EPUB-Spezifikation, und Prüfer
    lehnen ein Archiv ab, das sich nicht daran hält.
    """
    ziel = Path(ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    if ziel.exists():
        ziel.unlink()

    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as archiv:
        for name in unkomprimiert:
            archiv.writestr(zipfile.ZipInfo(name), dateien[name],
                            compress_type=zipfile.ZIP_STORED)
        for name, inhalt in dateien.items():
            if name in unkomprimiert:
                continue
            archiv.writestr(name, inhalt)
    return ziel


CONTAINER = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/inhalt.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""


def opf_bauen(cfg, kennung, eintraege, *, fest=False, umschlag="cover.jpg"):
    """Das Paketdokument: Metadaten, Dateiliste, Lesereihenfolge."""
    heute = date.today().isoformat()
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" '
        'properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '<item id="stil" href="stil.css" media-type="text/css"/>',
        f'<item id="umschlagbild" href="{umschlag}" media-type="image/jpeg" '
        'properties="cover-image"/>',
    ]
    ruecken = []
    for eintrag in eintraege:
        eigenschaften = ""
        if fest:
            eigenschaften = ' properties="rendition:layout-pre-paginated"'
        manifest.append(
            f'<item id="{eintrag["id"]}" href="{eintrag["datei"]}" '
            f'media-type="application/xhtml+xml"{eigenschaften}/>')
        ruecken.append(f'<itemref idref="{eintrag["id"]}"/>')
        for bild in eintrag.get("bilder", []):
            manifest.append(
                f'<item id="{bild["id"]}" href="{bild["datei"]}" '
                'media-type="image/jpeg"/>')

    layout = ""
    if fest:
        layout = ("\n    <meta property=\"rendition:layout\">pre-paginated</meta>"
                  "\n    <meta property=\"rendition:orientation\">auto</meta>"
                  "\n    <meta property=\"rendition:spread\">none</meta>")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0"
         unique-identifier="buchid" xml:lang="de"
         prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="buchid">{kennung}</dc:identifier>
    <dc:title>{html.escape(cfg["titel"])} — {html.escape(cfg["untertitel"])}</dc:title>
    <dc:creator>{html.escape(cfg["autor"])}</dc:creator>
    <dc:language>de</dc:language>
    <dc:publisher>{html.escape(cfg["impressum"]["name"])}</dc:publisher>
    <dc:date>{cfg["jahr"]}</dc:date>
    <dc:rights>© {cfg["jahr"]} {html.escape(cfg["impressum"]["name"])}</dc:rights>
    <meta property="dcterms:modified">{heute}T00:00:00Z</meta>
    <meta name="cover" content="umschlagbild"/>{layout}
  </metadata>
  <manifest>
    {chr(10).join("    " + z for z in manifest).strip()}
  </manifest>
  <spine toc="ncx">
    {chr(10).join("    " + z for z in ruecken).strip()}
  </spine>
</package>
"""


def nav_bauen(cfg, eintraege):
    """EPUB-3-Navigation. Nur echte Kapitel, keine Titelei."""
    punkte = []
    for eintrag in eintraege:
        if not eintrag.get("im_verzeichnis"):
            continue
        klasse = ' class="teil"' if eintrag.get("ist_teil") else ""
        punkte.append(f'<li{klasse}><a href="{eintrag["datei"]}">'
                      f'{html.escape(eintrag["titel"])}</a></li>')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="de" lang="de">
<head><title>Inhalt</title><meta charset="utf-8"/>
<link rel="stylesheet" type="text/css" href="stil.css"/></head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Inhalt</h1>
    <ol>
      {chr(10).join("      " + p for p in punkte).strip()}
    </ol>
  </nav>
</body>
</html>
"""


def ncx_bauen(cfg, kennung, eintraege):
    """Ältere Kindle-Geräte lesen das NCX statt der EPUB-3-Navigation."""
    punkte = []
    nummer = 0
    for eintrag in eintraege:
        if not eintrag.get("im_verzeichnis"):
            continue
        nummer += 1
        punkte.append(
            f'<navPoint id="nav{nummer}" playOrder="{nummer}">'
            f'<navLabel><text>{html.escape(eintrag["titel"])}</text></navLabel>'
            f'<content src="{eintrag["datei"]}"/></navPoint>')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="de">
  <head>
    <meta name="dtb:uid" content="{kennung}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{html.escape(cfg["titel"])}</text></docTitle>
  <navMap>
    {chr(10).join("    " + p for p in punkte).strip()}
  </navMap>
</ncx>
"""


def seite_bauen(titel, koerper, *, klasse="", kopf_extra=""):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="de" lang="de">
<head>
<title>{html.escape(titel)}</title>
<meta charset="utf-8"/>
<link rel="stylesheet" type="text/css" href="stil.css"/>{kopf_extra}
</head>
<body{f' class="{klasse}"' if klasse else ""}>
{koerper}
</body>
</html>
"""


# --- Band 1: fließender Text -------------------------------------------------
STIL_FLIESSEND = """/* Reflowable: keine festen Größen, keine Seitenzahlen.
   Alles in em und Prozent, damit die Schriftgrößeneinstellung des Lesers
   wirkt. Farben nur da, wo sie auch auf einem Graustufendisplay als
   Grauwert funktionieren. */
body { margin: 0 1em; line-height: 1.5; widows: 2; orphans: 2; }
h1, h2, h3 { font-family: sans-serif; color: #2F7A3E; line-height: 1.25;
             page-break-after: avoid; break-after: avoid; }
h1 { font-size: 1.6em; margin: 1.2em 0 0.8em; }
h2 { font-size: 1.2em; margin: 1.4em 0 0.4em; }
h3 { font-size: 1.0em; margin: 1.2em 0 0.3em; color: #5A5A5A; }
/* Kein text-align: justify. Der Blocksatz kommt ohne Trennung aus dem
   Stylesheet nicht gut heraus — auf schmalen Displays reißen Löcher in die
   Zeilen. Kindle setzt selbst und trennt dabei; die Entscheidung gehört
   dorthin und nicht hierher. */
p { margin: 0 0 0.7em; }
ul, ol { margin: 0 0 0.8em 1.2em; padding: 0; }
li { margin-bottom: 0.3em; }
hr { border: 0; border-top: 1px solid #C8C8C8; margin: 1.4em 20%; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0;
        font-size: 0.85em; }
th, td { border: 1px solid #C8C8C8; padding: 0.3em 0.4em;
         text-align: left; vertical-align: top; }
th { font-family: sans-serif; background: #EEF4EA; }
blockquote { margin: 1em 0; padding: 0.6em 0.9em; background: #EEF4EA;
             border-left: 3px solid #2F7A3E; }
blockquote p { margin: 0 0 0.4em; text-align: left; }
blockquote p:last-child { margin-bottom: 0; }
blockquote p.kastentitel { font-family: sans-serif; font-weight: bold;
                           color: #2F7A3E; }
.kapitelnummer { font-family: sans-serif; font-weight: bold; font-size: 0.8em;
                 color: #6FA85E; letter-spacing: 0.08em; margin-bottom: 0.2em; }
.teil { text-align: center; margin-top: 25%; }
.teil h1 { font-size: 1.15em; color: #6FA85E; letter-spacing: 0.12em; }
.teil h2 { font-size: 1.8em; color: #2F7A3E; margin-top: 0.2em; }
.titelseite { text-align: center; margin-top: 18%; }
.titelseite h1 { font-size: 2em; }
.titelseite .untertitel { font-family: sans-serif; font-size: 1.1em;
                          color: #5A5A5A; margin: 0.6em 0 2em; }
.titelseite .autor { font-family: sans-serif; font-weight: bold;
                     font-size: 1.1em; }
.umschlag { margin: 0; padding: 0; text-align: center; }
.umschlag img { max-width: 100%; height: auto; }
.klein { font-size: 0.85em; color: #5A5A5A; }
.leerzeile { height: 1em; }
nav ol { list-style: none; margin-left: 0; }
nav li.teil { text-align: left; margin-top: 1em; font-weight: bold;
              font-family: sans-serif; }
ul.verzeichnis { list-style: none; margin-left: 0; }
ul.verzeichnis li { margin-bottom: 0.35em; }
ul.verzeichnis li.teil { font-family: sans-serif; font-weight: bold;
                         color: #2F7A3E; margin: 1.1em 0 0.4em;
                         text-align: left; }
/* Verweisfarbe ausdrücklich setzen: Sonst färbt der Reader die Einträge
   in seinem Linkblau, und das Verzeichnis sieht aus wie eine Linksammlung
   statt wie ein Inhaltsverzeichnis. */
ul.verzeichnis a { text-decoration: none; color: #1A1A1A; }
ul.verzeichnis li.teil a { color: #2F7A3E; }
"""


def markdown_zu_xhtml(text):
    """Markdown → XHTML-Fragment.

    markdown-it liefert mit dem commonmark-Preset bereits XHTML-konforme
    Selbstschließer (<hr />, <br />). Nachbearbeitet werden nur zwei Dinge:
    die eigenen {{…}}-Marker und die Titelzeile im Hinweiskasten.
    """
    md = MarkdownIt("commonmark").enable("table").enable("strikethrough")

    # Seitenumbrüche bestimmt im E-Book der Reader, nicht der Satz.
    text = re.sub(r"(?m)^[ \t]*\{\{SEITENUMBRUCH\}\}[ \t]*$", "", text)
    text = re.sub(r"(?m)^[ \t]*\{\{LEERZEILE\}\}[ \t]*$",
                  '<div class="leerzeile"></div>', text)

    roh = md.render(text)

    # Hinweiskasten mit Titelzeile: „Kurz gefasst:" als erster Absatz, der auf
    # einen Doppelpunkt endet — dieselbe Regel wie im Druckbuch.
    def kastentitel(treffer):
        inhalt = treffer.group(1)
        return re.sub(r"^<p>([^<]*:)</p>", r'<p class="kastentitel">\1</p>',
                      inhalt, count=1)

    roh = re.sub(r"<blockquote>\n(.*?)</blockquote>",
                 lambda m: "<blockquote>\n" + kastentitel(m) + "</blockquote>",
                 roh, flags=re.S)
    return roh


def verzeichnis_bauen(kapitel, namen):
    """Verlinktes Inhaltsverzeichnis im Buch selbst.

    Die Navigation des Readers ersetzt es nicht ganz: Sie ist ein Menü, das
    man aufrufen muss. Ein Verzeichnis zu Beginn des Buchs zeigt beim
    Durchblättern, was einen erwartet — und KDP empfiehlt es ausdrücklich.
    Ohne Seitenzahlen, die gibt es hier nicht.
    """
    zeilen = ['<ul class="verzeichnis">']
    for kap in kapitel:
        meta = kap["meta"]
        if meta["typ"] == "titelei":
            continue
        titel = meta.get("titel", "")
        if meta["typ"] == "teil":
            zeilen.append(f'<li class="teil"><a href="{namen[id(kap)]}.xhtml">'
                          f'{html.escape(titel)}</a></li>')
        else:
            nummer = f'{meta["nummer"]}. ' if meta.get("nummer") else ""
            zeilen.append(f'<li><a href="{namen[id(kap)]}.xhtml">'
                          f'{html.escape(nummer + titel)}</a></li>')
    zeilen.append("</ul>")
    return "\n".join(zeilen)


def band1_bauen(cfg, kapitel, umschlagbild, ziel):
    dateien = {
        "mimetype": b"application/epub+zip",
        "META-INF/container.xml": CONTAINER,
        "OEBPS/stil.css": STIL_FLIESSEND,
        "OEBPS/cover.jpg": Path(umschlagbild).read_bytes(),
    }
    eintraege = []

    # Umschlagseite: Kindle zeigt das Titelbild ohnehin, aber ein Buch, das
    # beim Aufschlagen mit dem Impressum beginnt, wirkt unfertig.
    dateien["OEBPS/umschlag.xhtml"] = seite_bauen(
        cfg["titel"],
        f'<div class="umschlag"><img src="cover.jpg" '
        f'alt="{html.escape(cfg["titel"])}"/></div>',
        klasse="umschlag")
    eintraege.append({"id": "umschlag", "datei": "umschlag.xhtml",
                      "titel": "Umschlag", "im_verzeichnis": False})

    # Erst die Dateinamen vergeben, dann rendern: Das Inhaltsverzeichnis
    # verlinkt Kapitel, die beim Rendern noch nicht an der Reihe waren.
    namen = {id(kap): f"kap{nummer:02d}" for nummer, kap in enumerate(kapitel, 1)}
    verzeichnis = verzeichnis_bauen(kapitel, namen)

    for nummer, kap in enumerate(kapitel, 1):
        meta = kap["meta"]
        name = namen[id(kap)]
        rumpf = markdown_zu_xhtml(kap["text"]).replace(
            "{{INHALTSVERZEICHNIS}}", verzeichnis)

        if meta["typ"] == "teil":
            klasse, im_verzeichnis, ist_teil = "teil", True, True
        elif meta["typ"] == "titelei":
            klasse, im_verzeichnis, ist_teil = "", False, False
            if meta.get("layout") == "titelseite":
                klasse = "titelseite"
        else:
            klasse, im_verzeichnis, ist_teil = "", True, False
            if meta.get("nummer"):
                rumpf = (f'<p class="kapitelnummer">KAPITEL {meta["nummer"]}</p>\n'
                         + rumpf)

        dateien[f"OEBPS/{name}.xhtml"] = seite_bauen(
            meta.get("titel", cfg["titel"]), rumpf, klasse=klasse)
        eintraege.append({
            "id": name, "datei": f"{name}.xhtml",
            "titel": meta.get("titel", ""),
            "im_verzeichnis": im_verzeichnis, "ist_teil": ist_teil,
        })

    kennung = KENNUNG.format(band="b001", jahr=cfg["jahr"])
    dateien["OEBPS/nav.xhtml"] = nav_bauen(cfg, eintraege)
    dateien["OEBPS/toc.ncx"] = ncx_bauen(cfg, kennung, eintraege)
    dateien["OEBPS/inhalt.opf"] = opf_bauen(cfg, kennung, eintraege)
    return epub_schreiben(ziel, dateien), eintraege


# --- Band 3: fließender Text mit verlinkten Registern ------------------------
STIL_REZEPTE = STIL_FLIESSEND + """
/* Rezeptblock. Anders als im Druck steht der Name als Sprungziel: Im E-Book
   sind die Register keine Seitenzahlen zum Nachschlagen, sondern Verweise
   zum Antippen — das ist der eine Punkt, in dem die Ausgabe dem Druck
   überlegen ist. */
.rezept { margin: 1.8em 0 0; }
.rezept h2 { margin: 0 0 0.1em; font-size: 1.25em; }
.rezept .meta { font-family: sans-serif; font-size: 0.78em; color: #5A5A5A;
                letter-spacing: 0.04em; text-transform: uppercase;
                border-bottom: 1px solid #C8C8C8; padding-bottom: 0.4em;
                margin: 0 0 0.8em; }
.rezept h3 { font-size: 0.8em; letter-spacing: 0.08em; color: #6FA85E;
             margin: 1em 0 0.3em; }
.rezept ul { list-style: none; margin-left: 0.2em; }
.rezept ul li::before { content: "·  "; color: #6FA85E; }
.rezept ol { margin-left: 1.4em; }
.rezept .tipp { font-size: 0.9em; font-style: italic; color: #5A5A5A;
                margin-top: 0.6em; }
/* columns mit Mindestbreite statt fester Spaltenzahl: Auf einem breiten
   Bildschirm stehen zwei Spalten, auf einem schmalen E-Reader eine. Feste
   `columns: 2` würden dort zwei unlesbar enge Spalten erzwingen. */
.teilinhalt { list-style: none; margin: 1.2em 0 0 0; padding: 0;
              columns: 15em; column-gap: 1.5em; }
.teilinhalt li { margin-bottom: 0.3em; break-inside: avoid; font-size: 0.95em; }
.teilinhalt a { text-decoration: none; color: #1A1A1A; }
.register { list-style: none; margin-left: 0; padding: 0; }
.register li { margin-bottom: 0.35em; }
.register a { text-decoration: none; color: #1A1A1A; }
.register .wert { font-family: sans-serif; font-size: 0.82em; color: #5A5A5A; }
"""


def marke(text):
    """Sprungziel aus einem Rezeptnamen — stabil und ohne Sonderzeichen."""
    ersatz = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}
    klein = "".join(ersatz.get(z, z) for z in text.lower())
    return "r-" + re.sub(r"[^a-z0-9]+", "-", klein).strip("-")


def rezept_xhtml(rezept, farbmarke):
    zeilen = [f'<div class="rezept" id="{marke(rezept["name"])}">',
              f'<h2>{html.escape(rezept["name"])}</h2>']
    teile = [farbmarke[rezept["tagesfarbe"]][0],
             f'{rezept["portionen"]} Portion'
             + ("en" if rezept["portionen"] > 1 else "")]
    if rezept.get("zeit_min"):
        teile.append(f'{rezept["zeit_min"]} Min.')
    if rezept.get("eiweiss_g"):
        teile.append(f'ca. {rezept["eiweiss_g"]} g Eiweiß')
    zeilen.append('<p class="meta">' + " · ".join(html.escape(t) for t in teile)
                  + "</p>")

    zeilen.append("<h3>ZUTATEN</h3><ul>")
    zeilen += [f"<li>{html.escape(z)}</li>" for z in rezept["zutaten"]]
    zeilen.append("</ul>")

    zeilen.append("<h3>ZUBEREITUNG</h3><ol>")
    zeilen += [f"<li>{html.escape(s)}</li>" for s in rezept["schritte"]]
    zeilen.append("</ol>")

    if rezept.get("tipp"):
        zeilen.append(f'<p class="tipp"><b>Tipp:</b> '
                      f'{html.escape(rezept["tipp"])}</p>')
    zeilen.append("</div>")
    return "\n".join(zeilen)


def register_xhtml(register, art):
    """Register als Liste von Verweisen statt als Tabelle mit Seitenzahlen."""
    if art == "zeit":
        gruppen = [(10, "In 10 Minuten oder schneller"),
                   (20, "11 bis 20 Minuten"), (30, "21 bis 30 Minuten"),
                   (10**6, "Länger als 30 Minuten")]
        schluessel = lambda e: e["zeit"] or 10**6            # noqa: E731
        wert = lambda e: f'{e["zeit"]} Min.' if e["zeit"] else "—"  # noqa: E731
    elif art == "eiweiss":
        gruppen = [(-30, "30 Gramm und mehr"), (-20, "20 bis 29 Gramm"),
                   (-10, "10 bis 19 Gramm"), (0, "Unter 10 Gramm"),
                   (10**6, "Ohne Angabe")]
        schluessel = lambda e: -(e["eiweiss"] or 0) if e["eiweiss"] else 10**6  # noqa: E731
        wert = lambda e: f'{e["eiweiss"]} g' if e["eiweiss"] else "—"  # noqa: E731
    else:
        zeilen = ['<ul class="register">']
        for e in sorted(register, key=lambda x: x["name"].lower()):
            zeilen.append(
                f'<li><a href="{e["datei"]}#{marke(e["name"])}">'
                f'{html.escape(e["name"])}</a> '
                f'<span class="wert">{html.escape(e["teil"])}</span></li>')
        zeilen.append("</ul>")
        return "\n".join(zeilen)

    zeilen, offen = [], sorted(register, key=lambda e: (schluessel(e),
                                                        e["name"].lower()))
    for grenze, titel in gruppen:
        teil = [e for e in offen if schluessel(e) <= grenze]
        if not teil:
            continue
        offen = [e for e in offen if e not in teil]
        zeilen.append(f"<h3>{html.escape(titel.upper())}</h3>")
        zeilen.append('<ul class="register">')
        for e in teil:
            zeilen.append(
                f'<li><a href="{e["datei"]}#{marke(e["name"])}">'
                f'{html.escape(e["name"])}</a> '
                f'<span class="wert">{html.escape(wert(e))}</span></li>')
        zeilen.append("</ul>")
    return "\n".join(zeilen)


def band3_bauen(cfg, rahmen, abschnitte, farbmarke, umschlagbild, ziel):
    dateien = {
        "mimetype": b"application/epub+zip",
        "META-INF/container.xml": CONTAINER,
        "OEBPS/stil.css": STIL_REZEPTE,
        "OEBPS/cover.jpg": Path(umschlagbild).read_bytes(),
    }
    eintraege = [{"id": "umschlag", "datei": "umschlag.xhtml",
                  "titel": "Umschlag", "im_verzeichnis": False}]
    dateien["OEBPS/umschlag.xhtml"] = seite_bauen(
        cfg["titel"],
        f'<div class="umschlag"><img src="cover.jpg" '
        f'alt="{html.escape(cfg["titel"])}"/></div>', klasse="umschlag")

    vorne = [k for k in rahmen if k["meta"].get("position", "vorne") == "vorne"]
    hinten = [k for k in rahmen if k["meta"].get("position") == "hinten"]

    for nummer, kap in enumerate(vorne, 1):
        name = f"v{nummer:02d}"
        klasse = ("titelseite" if kap["meta"].get("layout") == "titelseite"
                  else "")
        dateien[f"OEBPS/{name}.xhtml"] = seite_bauen(
            kap["meta"].get("titel", cfg["titel"]),
            markdown_zu_xhtml(kap["text"]), klasse=klasse)
        eintraege.append({
            "id": name, "datei": f"{name}.xhtml",
            "titel": kap["meta"].get("titel", ""),
            "im_verzeichnis": nummer > 1, "ist_teil": False})

    # Rezeptteile — je Teil eine Datei, jedes Rezept ein Sprungziel darin.
    register = []
    for nummer, abschnitt in enumerate(abschnitte, 1):
        name = f"teil{nummer}"
        datei = f"{name}.xhtml"
        rumpf = [f'<h1>{html.escape(abschnitt["teil"])}</h1>']
        if abschnitt.get("einleitung"):
            rumpf.append(markdown_zu_xhtml(abschnitt["einleitung"]))
        rumpf.append('<ul class="teilinhalt">')
        rumpf += [f'<li><a href="#{marke(r["name"])}">'
                  f'{html.escape(r["name"])}</a></li>'
                  for r in abschnitt["rezepte"]]
        rumpf.append("</ul>")
        for r in abschnitt["rezepte"]:
            rumpf.append(rezept_xhtml(r, farbmarke))
            register.append({"name": r["name"], "teil": abschnitt["teil"],
                             "zeit": r.get("zeit_min"),
                             "eiweiss": r.get("eiweiss_g"), "datei": datei})
        dateien[f"OEBPS/{datei}"] = seite_bauen(
            abschnitt["teil"], "\n".join(rumpf))
        eintraege.append({"id": name, "datei": datei,
                          "titel": abschnitt["teil"],
                          "im_verzeichnis": True, "ist_teil": True})

    for nummer, kap in enumerate(hinten, 1):
        name = f"h{nummer:02d}"
        text = kap["text"]
        for marker, art in (("{{REZEPTREGISTER}}", "alphabetisch"),
                            ("{{REGISTER_ZEIT}}", "zeit"),
                            ("{{REGISTER_EIWEISS}}", "eiweiss")):
            if marker in text:
                text = text.replace(marker, "\n\n{{PLATZ}}\n\n")
                rumpf = markdown_zu_xhtml(text).replace(
                    "<p>{{PLATZ}}</p>", register_xhtml(register, art))
                break
        else:
            rumpf = markdown_zu_xhtml(text)
        dateien[f"OEBPS/{name}.xhtml"] = seite_bauen(
            kap["meta"].get("titel", ""), rumpf)
        eintraege.append({"id": name, "datei": f"{name}.xhtml",
                          "titel": kap["meta"].get("titel", ""),
                          "im_verzeichnis": True, "ist_teil": False})

    kennung = KENNUNG.format(band="b003", jahr=cfg["jahr"])
    dateien["OEBPS/nav.xhtml"] = nav_bauen(cfg, eintraege)
    dateien["OEBPS/toc.ncx"] = ncx_bauen(cfg, kennung, eintraege)
    dateien["OEBPS/inhalt.opf"] = opf_bauen(cfg, kennung, eintraege)
    return epub_schreiben(ziel, dateien), eintraege, register


# --- Band 2: feste Seiten ----------------------------------------------------
STIL_FEST = """/* pre-paginated: Jede Seite ist ein Bild, das die Fläche füllt. */
html, body { margin: 0; padding: 0; height: 100%; }
body { background: #FFFFFF; }
img.seite { width: 100%; height: 100%; display: block; }
nav ol { list-style: none; margin-left: 0; font-family: sans-serif; }
"""


def band2_bauen(cfg, pdf, umschlagbild, ziel, *, dpi=150, qualitaet=82):
    import io

    import fitz
    from PIL import Image

    dokument = fitz.open(str(pdf))
    breite_pt = dokument[0].rect.width
    hoehe_pt = dokument[0].rect.height
    skala = dpi / 72
    breite_px, hoehe_px = round(breite_pt * skala), round(hoehe_pt * skala)

    dateien = {
        "mimetype": b"application/epub+zip",
        "META-INF/container.xml": CONTAINER,
        "OEBPS/stil.css": STIL_FEST,
        "OEBPS/cover.jpg": Path(umschlagbild).read_bytes(),
    }
    eintraege = [{"id": "umschlag", "datei": "umschlag.xhtml",
                  "titel": "Umschlag", "im_verzeichnis": False,
                  "bilder": []}]

    sicht = (f'\n<meta name="viewport" content="width={breite_px}, '
             f'height={hoehe_px}"/>')
    dateien["OEBPS/umschlag.xhtml"] = seite_bauen(
        cfg["titel"],
        f'<img class="seite" src="cover.jpg" '
        f'alt="{html.escape(cfg["titel"])}"/>',
        kopf_extra=f'\n<meta name="viewport" content="width=1600, height=2560"/>')

    for nummer, seite in enumerate(dokument, 1):
        pix = seite.get_pixmap(matrix=fitz.Matrix(skala, skala), alpha=False)
        bild = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        puffer = io.BytesIO()
        bild.save(puffer, format="JPEG", quality=qualitaet, optimize=True)

        name = f"s{nummer:03d}"
        dateien[f"OEBPS/{name}.jpg"] = puffer.getvalue()
        dateien[f"OEBPS/{name}.xhtml"] = seite_bauen(
            f"Seite {nummer}",
            f'<img class="seite" src="{name}.jpg" alt="Seite {nummer}"/>',
            kopf_extra=sicht)
        eintraege.append({
            "id": name, "datei": f"{name}.xhtml", "titel": f"Seite {nummer}",
            "im_verzeichnis": False,
            "bilder": [{"id": f"{name}bild", "datei": f"{name}.jpg"}],
        })

    # Sprungmarken auf die Wochen statt auf jede einzelne Seite: Ein
    # Verzeichnis mit 92 Einträgen „Seite 1 … Seite 92" hilft niemandem.
    for eintrag in eintraege:
        eintrag["im_verzeichnis"] = False
    marken = wochenmarken(dokument,
                          kolumnentitel=(cfg["titel"], cfg["untertitel"]))
    for eintrag in eintraege:
        if eintrag["id"] in marken:
            eintrag["im_verzeichnis"] = True
            eintrag["titel"] = marken[eintrag["id"]]

    kennung = KENNUNG.format(band="b002", jahr=cfg["jahr"])
    dateien["OEBPS/nav.xhtml"] = nav_bauen(cfg, eintraege)
    dateien["OEBPS/toc.ncx"] = ncx_bauen(cfg, kennung, eintraege)
    dateien["OEBPS/inhalt.opf"] = opf_bauen(cfg, kennung, eintraege, fest=True)
    return epub_schreiben(ziel, dateien), eintraege


RAHMEN_MARKEN = (
    "Impressum", "Bitte zuerst lesen", "So nutzt du dieses Workbook",
    "Das Konzept in fünf Minuten", "Deine Startwerte", "Standortbestimmung",
    "Dein Verlauf über zwölf Wochen", "Wie es nach Woche 12 weitergeht",
    "Lebensmittel auf einen Blick", "Rechtliches und Hinweise",
)


def wochenmarken(dokument, kolumnentitel=()):
    """Findet die Seiten, auf denen ein Wochenauftakt oder Rahmenkapitel steht.

    Gesucht wird in den ersten Zeilen der Seite, nicht nur in der ersten: Ab
    der zweiten Seite eines Abschnitts steht der Kolumnentitel davor, und der
    ist beim Extrahieren die erste Textzeile. Genau daran sind beim ersten
    Versuch elf von zwölf Wochen durchgerutscht.
    """
    ueberspringen = {t.strip() for t in kolumnentitel if t.strip()}
    marken = {}
    for nummer, seite in enumerate(dokument, 1):
        zeilen = [z.strip() for z in (seite.get_text() or "").split("\n")
                  if z.strip()]
        zeilen = [z for z in zeilen if z not in ueberspringen][:3]
        if nummer == 1:
            marken["s001"] = "Titelseite"
            continue
        for zeile in zeilen:
            treffer = re.match(r"WOCHE (\d+) VON 12\s*·\s*(.+)", zeile)
            if treffer:
                phase = treffer.group(2).strip().capitalize()
                marken[f"s{nummer:03d}"] = f"Woche {treffer.group(1)} — {phase}"
                break
            if zeile in RAHMEN_MARKEN:
                marken[f"s{nummer:03d}"] = zeile
                break
    return marken


# --- Prüfung -----------------------------------------------------------------
def pruefen(epub):
    """Was ein EPUB-Prüfer als Erstes beanstandet."""
    from xml.etree import ElementTree

    befunde = []
    with zipfile.ZipFile(epub) as archiv:
        namen = archiv.namelist()
        if not namen or namen[0] != "mimetype":
            befunde.append("mimetype ist nicht der erste Eintrag im Archiv")
        else:
            info = archiv.getinfo("mimetype")
            if info.compress_type != zipfile.ZIP_STORED:
                befunde.append("mimetype ist komprimiert")
            if archiv.read("mimetype") != b"application/epub+zip":
                befunde.append("mimetype hat den falschen Inhalt")

        for pflicht in ("META-INF/container.xml", "OEBPS/inhalt.opf",
                        "OEBPS/nav.xhtml", "OEBPS/toc.ncx", "OEBPS/cover.jpg"):
            if pflicht not in namen:
                befunde.append(f"{pflicht} fehlt")

        # Jede XML-Datei muss wohlgeformt sein — ein einziges unmaskiertes
        # & im Titel reicht, damit der Reader die Datei verwirft.
        for name in namen:
            if not name.endswith((".xhtml", ".opf", ".ncx", ".xml")):
                continue
            try:
                ElementTree.fromstring(archiv.read(name))
            except ElementTree.ParseError as fehler:
                befunde.append(f"{name} ist kein gültiges XML: {fehler}")

        # Jede im Paket gelistete Datei muss es auch geben.
        if "OEBPS/inhalt.opf" in namen:
            opf = archiv.read("OEBPS/inhalt.opf").decode("utf-8")
            for href in re.findall(r'<item [^>]*href="([^"]+)"', opf):
                if f"OEBPS/{href}" not in namen:
                    befunde.append(f"im Paket gelistet, aber nicht vorhanden: {href}")
            ids = set(re.findall(r'<item id="([^"]+)"', opf))
            for idref in re.findall(r'<itemref idref="([^"]+)"', opf):
                if idref not in ids:
                    befunde.append(f"Lesereihenfolge nennt unbekannte id: {idref}")

    if Path(epub).stat().st_size > 650 * 1024 * 1024:
        befunde.append("größer als 650 MB — KDP nimmt das nicht an")
    return befunde


def main():
    kindle_cover_bauen()

    # Band 1
    cfg1 = yaml.safe_load((WURZEL / "buch" / "buch.yaml").read_text(encoding="utf-8"))
    kapitel = kapitel_laden(WURZEL / "buch" / "kapitel")
    ziel1 = WURZEL / "buch" / "out" / "stoffwechsel-reset-kindle.epub"
    ziel1, eintraege1 = band1_bauen(
        cfg1, kapitel, WURZEL / "buch" / "out" / "kindle-cover.jpg", ziel1)
    verzeichnis1 = sum(1 for e in eintraege1 if e["im_verzeichnis"])
    bericht("Band 1 — fließender Text", ziel1,
            f"{len(kapitel)} Kapitel, {verzeichnis1} Navigationspunkte")

    # Band 2
    cfg2 = yaml.safe_load(
        (WURZEL / "workbook" / "workbook.yaml").read_text(encoding="utf-8"))
    pdf2 = WURZEL / "workbook" / "out" / "workbook.pdf"
    if not pdf2.exists():
        print("Band 2: workbook.pdf fehlt — erst den Innenteil bauen.")
        return
    ziel2 = WURZEL / "workbook" / "out" / "workbook-kindle.epub"
    ziel2, eintraege2 = band2_bauen(
        cfg2, pdf2, WURZEL / "workbook" / "out" / "kindle-cover.jpg", ziel2)
    seiten = sum(1 for e in eintraege2 if e["id"].startswith("s"))
    verzeichnis2 = sum(1 for e in eintraege2 if e["im_verzeichnis"])
    bericht("Band 2 — feste Seiten", ziel2,
            f"{seiten} Seiten als Bild, {verzeichnis2} Navigationspunkte")

    # Band 3
    sys.path.insert(0, str(WURZEL / "rezepte" / "build"))
    import build_rezepte as br

    basis3 = WURZEL / "rezepte"
    cfg3 = yaml.safe_load((basis3 / "rezepte.yaml").read_text(encoding="utf-8"))
    rahmen3 = kapitel_laden(basis3 / "rahmen")
    abschnitte3 = br.rezeptdateien_laden(basis3 / "rezepte")
    ziel3 = basis3 / "out" / "rezeptbuch-kindle.epub"
    ziel3, eintraege3, register3 = band3_bauen(
        cfg3, rahmen3, abschnitte3, br.FARBMARKE,
        basis3 / "out" / "kindle-cover.jpg", ziel3)
    verzeichnis3 = sum(1 for e in eintraege3 if e["im_verzeichnis"])
    bericht("Band 3 — fließender Text", ziel3,
            f"{len(register3)} Rezepte, {verzeichnis3} Navigationspunkte")


def kindle_cover_bauen():
    import kindle_cover
    fehlt = [eintrag[2] for eintrag in kindle_cover.BAENDE
             if not (WURZEL / eintrag[2]).exists()]
    if fehlt:
        print("Titelbilder fehlen — erst kindle_cover.py laufen lassen.")
        raise SystemExit(1)


def bericht(name, pfad, zusatz):
    befunde = pruefen(pfad)
    print(f"{name}: {zusatz}, {pfad.stat().st_size / 1024:.0f} KB")
    print("  " + ("Struktur in Ordnung" if not befunde
                  else "ACHTUNG: " + "; ".join(befunde)))
    print(f"  → {pfad.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
