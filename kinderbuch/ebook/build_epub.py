#!/usr/bin/env python3
# Erzeugt eine reflowable EPUB-Fassung (Kindle/KDP) von
# "Pauli und das kleine Licht". Illustrationen werden aus den vorhandenen
# Inline-SVGs per Chromium zu PNGs gerendert und eingebettet.

import os, sys, shutil, subprocess, zipfile, uuid, html as _html

SRC = "/home/user/Mark-von-Daak/kinderbuch/buch-6x9"
ROOT = "/home/user/Mark-von-Daak/kinderbuch/ebook"
BUILD = os.path.join(ROOT, "_build")
OEBPS = os.path.join(BUILD, "OEBPS")
IMG = os.path.join(OEBPS, "images")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
OUT = os.path.join(ROOT, "Pauli-und-das-kleine-Licht.epub")

# Story-Daten aus dem Druck-Generator wiederverwenden.
os.chdir(SRC)                    # innenteil.html wird hier (harmlos) neu geschrieben
sys.path.insert(0, SRC)
import build_innenteil as b

# ---------- Aufbau der Build-Ordner ----------
if os.path.isdir(BUILD):
    shutil.rmtree(BUILD)
os.makedirs(IMG)
os.makedirs(os.path.join(BUILD, "META-INF"))

# ---------- Bild-Rendering ----------
def render(html_str, out_png, w, h, scale=2):
    tmp = os.path.join(ROOT, "_tmp_render.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html_str)
    subprocess.run(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
         f"--force-device-scale-factor={scale}", f"--window-size={w},{h}",
         f"--screenshot={out_png}", "file://" + tmp],
        check=True, stderr=subprocess.DEVNULL)
    os.remove(tmp)

def scene_html(inner, w, h, vb="0 0 400 300"):
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
            f'*{{margin:0;padding:0}}html,body{{width:{w}px;height:{h}px;overflow:hidden;background:#fff}}'
            f'svg.pic{{width:{w}px;height:{h}px;display:block}}'
            f'</style></head><body>{b.DEFS}<svg class="pic" viewBox="{vb}">{inner}</svg></body></html>')

# Kapitel-Illustrationen (14)
for i, ch in enumerate(b.CH, start=1):
    render(scene_html(b.SCENES[ch["scene"]], 600, 450), os.path.join(IMG, f"ch{i:02d}.png"), 600, 450)

# Figuren-Bilder
FIG = {
    "mouse":   '<use href="#mouse" x="34" y="34" width="232" height="232"/>',
    "firefly": '<use href="#firefly" x="70" y="70" width="160" height="160"/>',
    "toad":    '<use href="#toad" x="22" y="72" width="256" height="170"/>',
    "flower":  '<use href="#flower" x="78" y="18" width="144" height="264"/>',
    "starflower": '<use href="#starflower" x="78" y="18" width="144" height="264"/>',
}
for name, inner in FIG.items():
    render(scene_html(inner, 300, 300, vb="0 0 300 300"), os.path.join(IMG, f"fig_{name}.png"), 300, 300)

# E-Book-Cover (Hochformat 1600x2560 -> Fenster 800x1280, scale 2)
COVER_HTML = ('<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
  '*{margin:0;padding:0;box-sizing:border-box}'
  'html,body{width:800px;height:1280px;overflow:hidden;'
  'font-family:"Trebuchet MS","Segoe UI",Verdana,sans-serif;'
  'background:linear-gradient(180deg,#141f47 0%,#2b3a72 60%,#46568f 100%)}'
  '.wrap{position:relative;width:800px;height:1280px;overflow:hidden}'
  '.ground{position:absolute;left:0;bottom:0;width:100%;height:320px}'
  '.inner{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;'
  'text-align:center;padding:70px 56px 60px}'
  'h1{color:#fff;font-size:74px;line-height:1.05;text-shadow:0 4px 0 rgba(0,0,0,.18);margin-top:6px}'
  '.sub{color:#FFE9A0;font-size:30px;font-weight:600;margin-top:22px}'
  '.hero{width:560px;height:auto;margin-top:150px}'
  '.author{position:absolute;left:0;right:0;bottom:150px;color:#fff;font-size:34px;font-weight:700;text-align:center}'
  '.badge{position:absolute;left:0;right:0;bottom:84px;text-align:center}'
  '.badge span{background:#F6B93B;color:#4a3708;font-weight:800;font-size:22px;padding:9px 26px;border-radius:999px}'
  '</style></head><body>' + b.DEFS +
  '<div class="wrap">'
  '<svg style="position:absolute;inset:0" viewBox="0 0 800 1280" preserveAspectRatio="none">'
  '<g fill="#FFFFFF" opacity=".9">'
  '<use href="#spark" x="80" y="120" width="30" height="30"/><use href="#spark" x="300" y="90" width="20" height="20"/>'
  '<use href="#spark" x="560" y="120" width="26" height="26"/><use href="#spark" x="700" y="90" width="22" height="22"/>'
  '<use href="#spark" x="120" y="330" width="22" height="22"/><use href="#spark" x="660" y="360" width="26" height="26"/>'
  '<use href="#spark" x="80" y="520" width="20" height="20"/><use href="#spark" x="720" y="540" width="24" height="24"/>'
  '<use href="#spark" x="300" y="470" width="18" height="18"/><use href="#spark" x="500" y="470" width="20" height="20"/>'
  '<use href="#spark" x="180" y="600" width="18" height="18"/><use href="#spark" x="620" y="620" width="20" height="20"/>'
  '</g></svg>'
  '<svg class="ground" viewBox="0 0 800 320" preserveAspectRatio="none">'
  '<path d="M0 320 V150 Q160 90 360 130 Q520 90 800 130 V320 Z" fill="#22305a" opacity=".7"/>'
  '<path d="M0 320 V210 Q240 160 520 200 Q680 175 800 200 V320 Z" fill="#1a2547"/></svg>'
  '<div class="inner">'
  '<h1>Pauli und<br/>das kleine Licht</h1>'
  '<div class="sub">Eine Geschichte über Mut und Freundschaft</div>'
  '<svg class="hero" viewBox="0 0 400 264">'
  '<ellipse cx="200" cy="256" rx="192" ry="30" fill="#1a2547"/>'
  '<use href="#flower" x="138" y="6" width="124" height="155"/>'
  '<use href="#toad" x="228" y="156" width="156" height="104"/>'
  '<use href="#mouse" x="92" y="146" width="118" height="118"/>'
  '<use href="#firefly" x="196" y="112" width="60" height="60"/></svg>'
  '</div>'
  '<div class="author">Mark von Daak</div>'
  '<div class="badge"><span>Bilderbuch · ab 6 Jahren</span></div>'
  '</div></body></html>')
render(COVER_HTML, os.path.join(IMG, "cover.png"), 800, 1280, scale=2)

# ---------- XHTML-Helfer ----------
def page(title, body, cls=""):
    c = f' class="{cls}"' if cls else ""
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE html>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" '
            'xmlns:epub="http://www.idpf.org/2007/ops" lang="de">\n'
            f'<head><meta charset="utf-8"/><title>{title}</title>'
            '<link rel="stylesheet" type="text/css" href="style.css"/></head>\n'
            f'<body{c}>\n{body}\n</body></html>\n')

files = []   # (id, filename, media-type, in_spine, properties)
def write(fn, content, mid, spine=True, props=None):
    with open(os.path.join(OEBPS, fn), "w", encoding="utf-8") as f:
        f.write(content)
    files.append((mid, fn, "application/xhtml+xml", spine, props))

# Cover
write("cover.xhtml",
      page("Cover", '<div class="coverpage"><img src="images/cover.png" alt="Pauli und das kleine Licht"/></div>', cls="nomargin"),
      "cover")

# Titel
write("titlepage.xhtml",
      page("Titel",
           '<div class="titlepage">'
           '<h1 class="booktitle">Pauli und das kleine Licht</h1>'
           '<p class="subtitle">Eine Geschichte über Mut und Freundschaft</p>'
           '<p class="byline">Mark von Daak</p></div>'),
      "titlepage")

# Impressum
write("copyright.xhtml",
      page("Impressum",
           '<div class="imprint">'
           '<p><strong>Pauli und das kleine Licht</strong><br/>Eine Geschichte über Mut und Freundschaft</p>'
           '<p>Text und Illustrationen: Mark von Daak</p>'
           '<p class="small">1. Auflage · 2026<br/>© 2026 Mark von Daak. Alle Rechte vorbehalten.<br/>'
           'Kein Teil dieses Buches darf ohne schriftliche Genehmigung des Autors reproduziert '
           'oder verbreitet werden.<br/><br/>Die Figuren und die Handlung sind frei erfunden.</p></div>'),
      "copyright")

# Widmung
write("dedication.xhtml",
      page("Widmung",
           '<div class="dedication"><p>Für alle kleinen Mäuse,<br/>die glauben, '
           'sie seien nicht mutig genug.<br/>Ihr seid es.</p></div>'),
      "dedication")

# Figuren
write("figures.xhtml",
      page("Die Freunde dieser Geschichte",
           '<h1>Die Freunde dieser Geschichte</h1>'
           '<div class="fig"><img src="images/fig_mouse.png" alt="Pauli"/>'
           '<h3>Pauli</h3><p>Die kleinste und schüchternste Maus im Dorf unter der Wurzel – '
           'und mutiger, als sie ahnt.</p></div>'
           '<div class="fig"><img src="images/fig_firefly.png" alt="Luna"/>'
           '<h3>Luna</h3><p>Ein Glühwürmchen mit schwachem Licht, das Pauli zeigt: '
           'Schon ein winziger Schein reicht für den nächsten Schritt.</p></div>'
           '<div class="fig"><img src="images/fig_toad.png" alt="Bruno"/>'
           '<h3>Bruno</h3><p>Ein brummiger Kröterich mit weichem Herzen – und dem besten '
           'Rat der ganzen Reise.</p></div>'
           '<div class="fig"><img src="images/fig_flower.png" alt="Die Leuchtblume"/>'
           '<h3>Die Leuchtblume</h3><p>Das goldene Herz des Mäusedorfes – bis sie eines '
           'Nachts erlischt.</p></div>'),
      "figures")

# Kapitel
for i, ch in enumerate(b.CH, start=1):
    paras = []
    for pg in ch["pages"]:
        for p in pg:
            paras.append(f'<p>{p}</p>')
    caption = ch["vig"][1]
    body = (f'<p class="kicker">Kapitel {i}</p>\n'
            f'<h1>{ch["title"]}</h1>\n'
            f'<img class="illo" src="images/ch{i:02d}.png" alt="{ch["title"]}"/>\n'
            + "\n".join(paras) +
            f'\n<p class="quote">„{caption}“</p>')
    write(f"chapter{i:02d}.xhtml", page(f"Kapitel {i}: {ch['title']}", body), f"chapter{i:02d}")

# Ende
write("ende.xhtml",
      page("Ende", '<div class="theend"><p class="bigstar">🌟</p><h1>Ende</h1>'
           '<p class="endsub">…aber Paulis Mut geht weiter – jedes Mal, wenn du dich traust.</p></div>'),
      "ende")

# Gedicht
write("gedicht.xhtml",
      page("Ein kleines Mutmach-Gedicht",
           '<h1>Ein kleines Mutmach-Gedicht</h1><div class="poem">'
           "<p>Wenn's dunkel wird und bang ums Herz,<br/>dann denk an Pauli – trotz dem Schmerz:</p>"
           '<p>Du musst nicht groß, nicht furchtlos sein,<br/>geh einen Schritt – und nie allein.</p>'
           '<p>Ein kleines Licht, ein Freund dazu,<br/>und schon bist du mutig genug. Wie du.</p></div>'),
      "gedicht")

# Mut-Einmaleins
write("einmaleins.xhtml",
      page("Das kleine Mut-Einmaleins",
           '<h1>Das kleine Mut-Einmaleins</h1><ul class="lessons">'
           '<li><strong>Mut heißt nicht,</strong> keine Angst zu haben – sondern trotz der Angst weiterzugehen.</li>'
           '<li><strong>Du musst nicht</strong> den ganzen Weg sehen. Es genügt, den nächsten Schritt zu sehen.</li>'
           '<li><strong>Zusammen</strong> ist alles halb so dunkel. Geteilter Mut wird größer, nie kleiner.</li>'
           '<li><strong>Auch der Kleinste</strong> kann Großes vollbringen – vielleicht sogar gerade der Kleinste.</li>'
           '</ul>'),
      "einmaleins")

# Zum Weiterreden
write("weiterreden.xhtml",
      page("Zum Weiterreden",
           '<h1>Zum Weiterreden</h1><p class="intro">Nach dem Lesen könnt ihr gemeinsam überlegen:</p>'
           '<ul class="qlist">'
           '<li>Warum ist Pauli mutig, obwohl es Angst hat? Was bedeutet Mut für dich?</li>'
           '<li>Wie helfen sich Pauli, Luna und Bruno gegenseitig?</li>'
           '<li>Luna sagt: „Man muss nur den nächsten Schritt sehen.“ Wann hilft dir dieser Gedanke?</li>'
           '<li>Die Spinne fragt: Was wird größer, je mehr man es teilt?</li>'
           '<li>Gab es etwas, vor dem <em>du</em> Angst hattest – und du hast es trotzdem geschafft?</li>'
           '</ul>'),
      "weiterreden")

# Quiz
write("quiz.xhtml",
      page("Kennst du die Geschichte?",
           '<h1>Kennst du die Geschichte?</h1><p class="intro">Ein kleines Quiz – erinnerst du dich?</p>'
           '<ol class="qlist">'
           '<li>Wie heißt die Blume, die dem Dorf Licht schenkt?</li>'
           '<li>Wer setzt sich als Erster auf Paulis Nase?</li>'
           '<li>Wie hilft Bruno den beiden über den Bach?</li>'
           '<li>Welches Rätsel stellt die Spinne im Nebelwald?</li>'
           '<li>Was lernt Pauli am Ende über den Mut?</li></ol>'
           '<p class="hint">Tipp: Alle Antworten stehen in der Geschichte – blättere ruhig zurück!</p>'),
      "quiz")

# Wer war wer
write("werwarwer.xhtml",
      page("Wer war wer?",
           '<h1>Wer war wer?</h1>'
           '<div class="fig"><img src="images/fig_mouse.png" alt="Pauli"/><h3>Pauli</h3><p>die kleine, mutige Maus.</p></div>'
           '<div class="fig"><img src="images/fig_firefly.png" alt="Luna"/><h3>Luna</h3><p>das treue Glühwürmchen.</p></div>'
           '<div class="fig"><img src="images/fig_toad.png" alt="Bruno"/><h3>Bruno</h3><p>der brummige, gute Kröterich.</p></div>'
           '<div class="fig"><img src="images/fig_starflower.png" alt="Die Sternenblume"/><h3>Die Sternenblume</h3><p>der Funke der Hoffnung.</p></div>'),
      "werwarwer")

# Kolophon
write("kolophon.xhtml",
      page("Über dieses Buch",
           '<div class="colophon"><p class="deco">🐭 ✨ 🐸</p>'
           '<p>Geschrieben und illustriert für alle, die ihren ersten mutigen Schritt noch vor sich haben.</p>'
           '<p class="small">Pauli und das kleine Licht · © 2026 Mark von Daak</p></div>'),
      "kolophon")

# ---------- style.css ----------
CSS = '''@charset "utf-8";
body { font-family: Georgia, "Times New Roman", serif; margin: 0 1em; line-height: 1.5; color: #263445; }
body.nomargin { margin: 0; }
h1 { text-align: center; font-size: 1.5em; color: #2F9BD6; margin: 0.7em 0 0.4em; line-height: 1.15; }
.kicker { text-align: center; text-transform: uppercase; letter-spacing: 1px; font-size: 0.72em; font-weight: bold; color: #8a95a1; margin: 1.1em 0 0; }
p { text-align: center; margin: 0 0 0.85em; }
strong { color: #2F9BD6; }
img.illo { display: block; margin: 0.7em auto 1em; max-width: 100%; border-radius: 10px; }
.quote { font-style: italic; text-align: center; color: #3a4553; margin: 1.4em 1.2em 0.6em; font-size: 1.05em; }
.coverpage { text-align: center; margin: 0; padding: 0; }
.coverpage img { max-width: 100%; height: auto; }
.titlepage { text-align: center; margin-top: 22%; }
.booktitle { font-size: 2em; color: #2F9BD6; }
.subtitle { font-style: italic; color: #5D6B7B; }
.byline { margin-top: 2em; font-size: 1.1em; }
.imprint { font-size: 0.85em; color: #4a5563; text-align: center; margin-top: 15%; }
.imprint .small { font-size: 0.85em; color: #7a8290; }
.dedication { text-align: center; margin-top: 30%; font-style: italic; color: #5D6B7B; font-size: 1.15em; }
.fig { text-align: center; margin: 1.4em 0; }
.fig img { width: 38%; max-width: 150px; height: auto; }
.fig h3 { color: #17B6A0; margin: 0.3em 0 0.2em; }
.fig p { margin: 0 auto; max-width: 22em; }
.theend { text-align: center; margin-top: 22%; }
.theend .bigstar { font-size: 2.4em; margin: 0; }
.theend .endsub { font-style: italic; color: #5D6B7B; }
.poem { text-align: center; }
.poem p { font-style: italic; font-size: 1.1em; line-height: 1.8; }
.lessons, .qlist { text-align: left; margin: 0 auto; max-width: 26em; line-height: 1.55; }
.lessons li, .qlist li { margin-bottom: 0.6em; }
.lessons strong { color: #17B6A0; }
.intro { color: #5D6B7B; }
.hint { font-size: 0.85em; color: #8a93a0; font-style: italic; }
.colophon { text-align: center; margin-top: 22%; }
.colophon .deco { font-size: 1.8em; }
.colophon .small { color: #8a93a0; font-size: 0.85em; }
'''
with open(os.path.join(OEBPS, "style.css"), "w", encoding="utf-8") as f:
    f.write(CSS)

# ---------- nav.xhtml (EPUB3) ----------
nav_items = [("titlepage.xhtml", "Titel")]
nav_items += [(f"chapter{i:02d}.xhtml", f"Kapitel {i}: {ch['title']}") for i, ch in enumerate(b.CH, start=1)]
nav_items += [("gedicht.xhtml", "Mutmach-Gedicht"), ("einmaleins.xhtml", "Das kleine Mut-Einmaleins"),
              ("weiterreden.xhtml", "Zum Weiterreden"), ("quiz.xhtml", "Kennst du die Geschichte?"),
              ("werwarwer.xhtml", "Wer war wer?")]
nav_lis = "\n".join(f'<li><a href="{href}">{_html.escape(t)}</a></li>' for href, t in nav_items)
nav = ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
       '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="de">\n'
       '<head><meta charset="utf-8"/><title>Inhalt</title></head><body>\n'
       '<nav epub:type="toc" id="toc"><h1>Inhalt</h1>\n<ol>\n' + nav_lis + '\n</ol></nav>\n'
       '<nav epub:type="landmarks" hidden="hidden"><ol>'
       '<li><a epub:type="cover" href="cover.xhtml">Cover</a></li>'
       '<li><a epub:type="bodymatter" href="chapter01.xhtml">Anfang</a></li></ol></nav>\n'
       '</body></html>\n')
with open(os.path.join(OEBPS, "nav.xhtml"), "w", encoding="utf-8") as f:
    f.write(nav)

# ---------- toc.ncx (EPUB2-Fallback) ----------
BOOK_ID = "urn:uuid:" + str(uuid.uuid4())
navpoints = []
for idx, (href, t) in enumerate(nav_items, start=1):
    navpoints.append(f'<navPoint id="np{idx}" playOrder="{idx}"><navLabel><text>{_html.escape(t)}</text></navLabel><content src="{href}"/></navPoint>')
ncx = ('<?xml version="1.0" encoding="utf-8"?>\n'
       '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
       f'<head><meta name="dtb:uid" content="{BOOK_ID}"/></head>\n'
       '<docTitle><text>Pauli und das kleine Licht</text></docTitle>\n'
       '<navMap>\n' + "\n".join(navpoints) + '\n</navMap></ncx>\n')
with open(os.path.join(OEBPS, "toc.ncx"), "w", encoding="utf-8") as f:
    f.write(ncx)

# ---------- content.opf ----------
manifest = []
manifest.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
manifest.append('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
manifest.append('<item id="css" href="style.css" media-type="text/css"/>')
manifest.append('<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>')
imgs = sorted(fn for fn in os.listdir(IMG) if fn != "cover.png")
for fn in imgs:
    manifest.append(f'<item id="img_{fn[:-4]}" href="images/{fn}" media-type="image/png"/>')
for mid, fn, mt, spine, props in files:
    p = f' properties="{props}"' if props else ""
    manifest.append(f'<item id="{mid}" href="{fn}" media-type="{mt}"{p}/>')

spine = "".join(f'<itemref idref="{mid}"/>' for mid, fn, mt, sp, props in files if sp)

DESC = ("Pauli ist die kleinste und schüchternste Maus im ganzen Dorf. Als das Licht der "
        "Leuchtblume erlischt, meldet sich ausgerechnet Pauli, um den rettenden Funken vom "
        "Nebelberg zu holen. Eine warmherzige Geschichte über Mut und Freundschaft für Kinder ab 6 Jahren.")
opf = ('<?xml version="1.0" encoding="utf-8"?>\n'
       '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">\n'
       '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
       f'<dc:identifier id="bookid">{BOOK_ID}</dc:identifier>\n'
       '<dc:title>Pauli und das kleine Licht</dc:title>\n'
       '<dc:language>de</dc:language>\n'
       '<dc:creator>Mark von Daak</dc:creator>\n'
       f'<dc:description>{_html.escape(DESC)}</dc:description>\n'
       '<meta property="dcterms:modified">2026-01-01T00:00:00Z</meta>\n'
       '<meta name="cover" content="cover-image"/>\n'
       '</metadata>\n<manifest>\n' + "\n".join(manifest) + '\n</manifest>\n'
       f'<spine toc="ncx">{spine}</spine>\n</package>\n')
with open(os.path.join(OEBPS, "content.opf"), "w", encoding="utf-8") as f:
    f.write(opf)

# ---------- container + mimetype ----------
with open(os.path.join(BUILD, "mimetype"), "w", encoding="utf-8") as f:
    f.write("application/epub+zip")
with open(os.path.join(BUILD, "META-INF", "container.xml"), "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
            '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>\n'
            '</container>\n')

# ---------- zippen ----------
if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, "w") as z:
    z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
    for r, _, fns in os.walk(BUILD):
        for fn in fns:
            full = os.path.join(r, fn)
            rel = os.path.relpath(full, BUILD)
            if rel == "mimetype":
                continue
            z.write(full, rel, compress_type=zipfile.ZIP_DEFLATED)

print("EPUB erstellt:", OUT)
print("XHTML-Seiten:", len(files), "| Bilder:", len(os.listdir(IMG)))
