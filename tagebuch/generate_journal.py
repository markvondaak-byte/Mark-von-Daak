# -*- coding: utf-8 -*-
"""
Generator für ein eigenständiges Achtsamkeits- / Dankbarkeitstagebuch
("Sechs Minuten für mich") als druckfertige KDP-Dateien.

Erzeugt:
  1. Innenseiten-PDF  (6x9", gespiegelte Ränder, KDP-Bundsteg)
  2. Cover-PDF        (Front + Rücken + Back, mit Beschnitt/Bleed)

Alle Texte, Impulse und das Layout sind eigenständig verfasst und
verwenden NICHT den markenrechtlich geschützten Titel eines Fremdprodukts.

Ausführen:  python3 generate_journal.py
"""

import os
import math
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --------------------------------------------------------------------------
# KONFIGURATION
# --------------------------------------------------------------------------
TITLE      = "Sechs Minuten für mich"
TITLE_DISP = "Sechs Minuten\nfür mich"          # Anzeige mit Zeilenumbruch
SUBTITLE   = ("Das tägliche Dankbarkeits- und Achtsamkeitstagebuch\n"
              "3 Minuten morgens  ·  3 Minuten abends")
AUTHOR_PLACEHOLDER = "________________________"
YEAR       = 2026
DAYS       = 180
WEEK_LEN   = 7

OUT_DIR    = os.path.dirname(os.path.abspath(__file__))
INTERIOR   = os.path.join(OUT_DIR, "innenseiten_6x9.pdf")
COVER      = os.path.join(OUT_DIR, "cover_6x9.pdf")

# --------------------------------------------------------------------------
# MASSE (Punkte, 72pt = 1 inch)
# --------------------------------------------------------------------------
PW, PH   = 6 * inch, 9 * inch          # Trim / Endformat
GUTTER   = 0.5   * inch                 # Bundsteg (innen) -> 151-300 Seiten
OUTER    = 0.375 * inch                 # Außenrand
TOP      = 0.55  * inch
BOTTOM   = 0.5   * inch

# --------------------------------------------------------------------------
# FARBEN (warm / motivierend)
# --------------------------------------------------------------------------
INK    = Color(0.22, 0.18, 0.15)        # warmes Dunkelbraun
SOFT   = Color(0.42, 0.36, 0.31)        # gedämpftes Braun
ACCENT = Color(0.76, 0.42, 0.31)        # Terracotta
GOLD   = Color(0.82, 0.62, 0.34)        # warmes Gold
SAND   = Color(0.965, 0.935, 0.885)     # Sand / Creme
SANDD  = Color(0.93, 0.89, 0.82)        # dunkleres Sand
LINE   = Color(0.80, 0.74, 0.66)        # Schreiblinie
LINEL  = Color(0.87, 0.82, 0.75)        # helle Linie
WHITE  = Color(1, 1, 1)

# --------------------------------------------------------------------------
# FONTS
# --------------------------------------------------------------------------
FDIR = "/usr/share/fonts/truetype/liberation"
pdfmetrics.registerFont(TTFont("Serif",   f"{FDIR}/LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("SerifB",  f"{FDIR}/LiberationSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("SerifI",  f"{FDIR}/LiberationSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Sans",    f"{FDIR}/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("SansB",   f"{FDIR}/LiberationSans-Bold.ttf"))

# --------------------------------------------------------------------------
# EIGENE TAGES-IMPULSE (original verfasst)
# --------------------------------------------------------------------------
IMPULSES = [
    "Jeder Morgen ist eine neue, leere Seite. Schreibe sie mit Absicht.",
    "Kleine Schritte, jeden Tag getan, tragen dich erstaunlich weit.",
    "Dankbarkeit verwandelt das, was du hast, in mehr als genug.",
    "Du musst nicht perfekt sein. Nur ein wenig freundlicher zu dir.",
    "Atme tief durch. Dieser Moment gehört ganz allein dir.",
    "Was du heute schätzt, wächst. Also schätze das Gute.",
    "Nicht jeder Tag ist gut, doch in jedem Tag steckt etwas Gutes.",
    "Fortschritt ist leiser als Perfektion, aber viel zuverlässiger.",
    "Beginne heute bei dem, was du beeinflussen kannst.",
    "Ein ruhiger Geist trifft die klareren Entscheidungen.",
    "Sei heute der Mensch, dem du morgens gern begegnest.",
    "Die kleinen Freuden sind in Wahrheit die großen.",
    "Gib dir selbst die Geduld, die du anderen so leicht schenkst.",
    "Heute zählt nicht, wie viel du schaffst, sondern wie du es tust.",
    "Ruhe ist keine verlorene Zeit, sondern gewonnene Kraft.",
    "Deine Aufmerksamkeit ist ein Geschenk. Wähle sorgsam, wem du es gibst.",
    "Aus einem dankbaren Herzen wachsen die schönsten Tage.",
    "Mut heißt oft nur: den ersten kleinen Schritt trotzdem gehen.",
    "Was du am Abend loslässt, muss der Morgen nicht mehr tragen.",
    "Freundlichkeit kostet dich nichts und verändert manchmal alles.",
    "Vergleiche dich mit dem, der du gestern warst.",
    "Ein guter Gedanke am Morgen färbt den ganzen Tag.",
    "Du darfst stolz sein auf den Weg, den du schon gegangen bist.",
    "Langsamer atmen, klarer denken, freier fühlen.",
    "Das Leben passiert genau jetzt, nicht irgendwann.",
    "Suche nicht den perfekten Tag, sondern das Gute im heutigen.",
    "Selbst ein kleiner Lichtblick reicht, um den Weg zu sehen.",
    "Was du pflegst, blüht. Pflege heute deine Zuversicht.",
    "Deine Ruhe ist deine Stärke. Bewahre sie.",
    "Jeder Tag, den du bewusst lebst, ist ein gewonnener Tag.",
    "Freue dich an dem, was schon da ist, bevor du mehr suchst.",
    "Ein ehrliches Danke ist ein kleines Wunder im Alltag.",
    "Du bist genug, so wie du heute Morgen aufgewacht bist.",
    "Manchmal ist Innehalten der produktivste Schritt.",
    "Gutes gedeiht dort, wo du hinschaust. Schau nach oben.",
    "Setze heute ein kleines Zeichen, das du morgen noch spürst.",
    "Der Weg wird leichter, wenn du dankbar auf ihn blickst.",
    "Lass dein heutiges Ich ein wenig stolzer werden.",
    "Zwischen Reiz und Reaktion liegt dein ruhiger Atemzug.",
    "Das Beste, das du geben kannst, ist deine volle Gegenwart.",
]

# --------------------------------------------------------------------------
# HILFSFUNKTIONEN
# --------------------------------------------------------------------------
class Book:
    def __init__(self, path):
        self.c = canvas.Canvas(path, pagesize=(PW, PH))
        self.page = 0

    def new(self):
        """Beginnt eine neue Seite und liefert (links, rechts, oben, unten)
        Ränder abhängig von recto/verso (gespiegelt)."""
        if self.page > 0:
            self.c.showPage()
        self.page += 1
        recto = (self.page % 2 == 1)         # ungerade = rechte Seite
        left  = GUTTER if recto else OUTER
        right = OUTER  if recto else GUTTER
        return left, PW - right, PH - TOP, BOTTOM

    def save(self):
        self.c.showPage()
        self.c.save()

    def page_number(self, left, right):
        """Dezente Seitenzahl unten außen."""
        c = self.c
        recto = (self.page % 2 == 1)
        c.setFont("Sans", 8)
        c.setFillColor(SOFT)
        y = BOTTOM - 16
        if recto:
            c.drawRightString(right, y, str(self.page))
        else:
            c.drawString(left, y, str(self.page))


def txt(c, x, y, s, font="Serif", size=11, color=INK, align="l"):
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "l":
        c.drawString(x, y, s)
    elif align == "c":
        c.drawCentredString(x, y, s)
    elif align == "r":
        c.drawRightString(x, y, s)


def writing_lines(c, x, w, y, n, gap=21, color=LINE):
    """Zeichnet n Schreiblinien, gibt y unterhalb zurück."""
    c.setStrokeColor(color)
    c.setLineWidth(0.6)
    for i in range(n):
        y -= gap
        c.line(x, y, x + w, y)
    return y


def dotted_rule(c, x1, x2, y, color=LINEL, w=0.8):
    c.setStrokeColor(color)
    c.setLineWidth(w)
    c.setDash(1, 3)
    c.line(x1, y, x2, y)
    c.setDash()


def sun(c, cx, cy, r, color=ACCENT):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.4)
    c.circle(cx, cy, r, stroke=1, fill=0)
    for k in range(8):
        a = k * math.pi / 4
        x1 = cx + math.cos(a) * (r + 2.2)
        y1 = cy + math.sin(a) * (r + 2.2)
        x2 = cx + math.cos(a) * (r + 5.5)
        y2 = cy + math.sin(a) * (r + 5.5)
        c.line(x1, y1, x2, y2)


def moon(c, cx, cy, r, color=ACCENT, bg=WHITE):
    """Sichelmond durch zwei überlappende Kreise."""
    c.saveState()
    c.setFillColor(color)
    c.circle(cx, cy, r, stroke=0, fill=1)
    c.setFillColor(bg)
    c.circle(cx + r * 0.55, cy + r * 0.25, r * 0.92, stroke=0, fill=1)
    c.restoreState()


def band(c, x, y, w, h, fill=SAND, radius=6):
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, radius, stroke=0, fill=1)


def wrap(c, text, font, size, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        test = (cur + " " + wd).strip()
        if c.stringWidth(test, font, size) <= maxw:
            cur = test
        else:
            lines.append(cur); cur = wd
    if cur:
        lines.append(cur)
    return lines


# --------------------------------------------------------------------------
# SEITEN-TEMPLATES
# --------------------------------------------------------------------------
def daily_page(bk, day, impulse, example=False):
    c = bk.c
    left, right, top, bottom = bk.new()
    w = right - left

    # ---- Kopfzeile ----
    y = top
    txt(c, left, y - 4, f"TAG {day:>3}", "SansB", 12, ACCENT, "l")
    txt(c, right, y - 4, "Datum:  ____  /  ____  /  ________", "Sans", 9.5, SOFT, "r")
    y -= 12
    c.setStrokeColor(SANDD); c.setLineWidth(1); c.line(left, y, right, y)

    # Wochentage zum Ankreuzen
    y -= 16
    days_lbl = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    step = w / 7.0
    for i, d in enumerate(days_lbl):
        cx = left + step * i + step / 2
        c.setStrokeColor(LINE); c.setLineWidth(0.8)
        c.circle(cx - 12, y + 3, 3.2, stroke=1, fill=0)
        txt(c, cx - 6, y, d, "Sans", 8.5, SOFT, "l")

    # ---- Impuls des Tages ----
    y -= 14
    bh = 34
    band(c, left, y - bh, w, bh, SAND)
    txt(c, left + w/2, y - 14, "GEDANKE FÜR HEUTE", "SansB", 7.5, ACCENT, "c")
    ly = y - 25
    for ln in wrap(c, impulse, "SerifI", 10.5, w - 30)[:2]:
        txt(c, left + w/2, ly, ln, "SerifI", 10.5, INK, "c")
        ly -= 12
    y -= bh + 14

    # ---- MORGEN ----
    sun(c, left + 7, y - 3, 6.5, ACCENT)
    txt(c, left + 22, y - 6, "MORGEN", "SansB", 12, INK, "l")
    txt(c, left + 92, y - 6, "3 Minuten", "Sans", 9, GOLD, "l")
    y -= 20

    def block(label, nlines, ex=None):
        nonlocal y
        txt(c, left, y, label, "SansB", 8.5, SOFT, "l")
        y -= 4
        y0 = y
        y = writing_lines(c, left, w, y, nlines)
        if example and ex:
            c.setFont("SerifI", 10)
            c.setFillColor(SOFT)
            yy = y0 - 15
            for e in ex[:nlines]:
                c.drawString(left + 4, yy, e)
                yy -= 21
        y -= 8

    block("Wofür bin ich heute dankbar?", 3,
          ["für den ruhigen Start in den Tag",
           "für meine Gesundheit", "für den Kaffee am Fenster"] if example else None)
    block("Was macht heute zu einem guten Tag?", 2,
          ["ein ehrliches Gespräch mit einem Freund",
           "meine Aufgabe konzentriert erledigen"] if example else None)
    block("Meine Affirmation für heute:", 1,
          ["Ich gehe ruhig und klar durch diesen Tag."] if example else None)

    # ---- Trennlinie ----
    y -= 2
    dotted_rule(c, left, right, y)
    y -= 14

    # ---- ABEND ----
    moon(c, left + 7, y - 3, 6.5, ACCENT)
    txt(c, left + 22, y - 6, "ABEND", "SansB", 12, INK, "l")
    txt(c, left + 92, y - 6, "3 Minuten", "Sans", 9, GOLD, "l")
    y -= 20

    block("Was war heute schön? Drei Momente:", 3,
          ["die Sonne am Mittag", "ein Lob bekommen",
           "gut gegessen und gekocht"] if example else None)
    block("Das habe ich heute gut gemacht / gelernt:", 2,
          ["ruhig geblieben in einer hektischen Lage",
           "bewusst eine Pause genommen"] if example else None)
    block("So mache ich es morgen noch besser:", 1,
          ["etwas früher schlafen gehen"] if example else None)

    # ---- Stimmung ----
    txt(c, left, y, "Meine Stimmung heute:", "SansB", 8.5, SOFT, "l")
    for i in range(5):
        cx = left + 118 + i * 16
        c.setStrokeColor(LINE); c.setLineWidth(0.9)
        c.circle(cx, y + 3, 5, stroke=1, fill=0)

    bk.page_number(left, right)


def weekly_page(bk, week):
    c = bk.c
    left, right, top, bottom = bk.new()
    w = right - left
    y = top

    band(c, left, y - 30, w, 30, SANDD)
    txt(c, left + 14, y - 20, "WOCHENRÜCKBLICK", "SansB", 12, INK, "l")
    txt(c, right - 14, y - 20, f"Woche {week}", "SerifI", 13, ACCENT, "r")
    y -= 52

    def sec(label, n):
        nonlocal y
        txt(c, left, y, label, "SansB", 9.5, ACCENT, "l")
        y -= 6
        y = writing_lines(c, left, w, y, n, gap=23)
        y -= 16

    sec("Meine drei schönsten Momente dieser Woche", 3)
    sec("Das habe ich diese Woche erreicht", 3)
    sec("Dafür bin ich besonders dankbar", 2)
    sec("Das nehme ich mir für nächste Woche vor", 3)

    txt(c, left, y, "Meine Wochenbilanz:", "SansB", 9.5, SOFT, "l")
    for i in range(5):
        cx = left + 110 + i * 20
        c.setStrokeColor(LINE); c.setLineWidth(1)
        c.circle(cx, y + 3, 6, stroke=1, fill=0)

    bk.page_number(left, right)


# --------------------------------------------------------------------------
# FRONT-MATTER
# --------------------------------------------------------------------------
def title_page(bk):
    c = bk.c
    left, right, top, bottom = bk.new()
    cx = (left + right) / 2

    c.setFillColor(SAND)
    c.rect(0, 0, PW, PH, stroke=0, fill=1)

    c.setStrokeColor(GOLD); c.setLineWidth(1.2)
    c.line(cx - 40, PH - 130, cx + 40, PH - 130)
    sun(c, cx, PH - 158, 9, ACCENT)

    c.setFillColor(INK)
    c.setFont("SerifB", 34)
    for i, ln in enumerate(TITLE_DISP.split("\n")):
        c.drawCentredString(cx, PH - 230 - i * 40, ln)

    c.setStrokeColor(ACCENT); c.setLineWidth(1)
    c.line(cx - 55, PH - 320, cx + 55, PH - 320)

    c.setFont("Serif", 12.5)
    c.setFillColor(SOFT)
    for i, ln in enumerate(SUBTITLE.split("\n")):
        c.drawCentredString(cx, PH - 350 - i * 20, ln)

    c.setFont("SansB", 11)
    c.setFillColor(ACCENT)
    c.drawCentredString(cx, 150, f"{DAYS} TAGE")
    c.setFont("Sans", 10)
    c.setFillColor(SOFT)
    c.drawCentredString(cx, 132, "Morgen- und Abendritual")


def owner_page(bk):
    c = bk.c
    left, right, top, bottom = bk.new()
    w = right - left
    y = top - 40
    txt(c, left + w/2, y, "Dieses Tagebuch gehört", "SerifI", 16, ACCENT, "c")
    y -= 60
    for lbl in ["Name", "Startdatum", "Mein Warum – warum ich dieses Ritual beginne"]:
        txt(c, left, y, lbl, "SansB", 9.5, SOFT, "l")
        y -= 6
        n = 3 if lbl.startswith("Mein Warum") else 1
        y = writing_lines(c, left, w, y, n, gap=24)
        y -= 26

    band(c, left, y - 70, w, 60, SAND)
    txt(c, left + w/2, y - 30, "„Ein kleines Ritual, täglich wiederholt,", "SerifI", 11.5, INK, "c")
    txt(c, left + w/2, y - 48, "wird mit der Zeit zu einer großen Veränderung.“", "SerifI", 11.5, INK, "c")


def copyright_page(bk):
    c = bk.c
    left, right, top, bottom = bk.new()
    w = right - left
    y = 260
    lines = [
        f"© {YEAR}  {AUTHOR_PLACEHOLDER}",
        "Alle Rechte vorbehalten.",
        "",
        "Kein Teil dieses Buches darf ohne schriftliche",
        "Genehmigung reproduziert oder vervielfältigt werden.",
        "",
        "1. Auflage",
        "",
        "Dieses Tagebuch dient der persönlichen Reflexion",
        "und ersetzt keine medizinische oder therapeutische",
        "Beratung.",
    ]
    for ln in lines:
        txt(c, left, y, ln, "Serif", 10, SOFT, "l")
        y -= 15


def intro_page(bk):
    c = bk.c
    left, right, top, bottom = bk.new()
    w = right - left
    y = top - 6
    txt(c, left, y, "Warum sechs Minuten genügen", "SerifB", 18, INK, "l")
    y -= 10
    c.setStrokeColor(ACCENT); c.setLineWidth(1.2); c.line(left, y, left + 60, y)
    y -= 24

    paras = [
        "Ein erfülltes Leben entsteht selten durch große, einmalige "
        "Entscheidungen. Viel häufiger wächst es aus kleinen Gewohnheiten, "
        "die wir Tag für Tag wiederholen. Genau hier setzt dieses Tagebuch an.",
        "Am Morgen richtest du deinen Blick in drei kurzen Schritten aus: "
        "Du wirst dir bewusst, wofür du dankbar bist, du entscheidest, was "
        "diesen Tag zu einem guten Tag macht, und du stärkst dich mit einer "
        "freundlichen Affirmation.",
        "Am Abend lässt du den Tag in drei Schritten ausklingen: Du "
        "erinnerst dich an schöne Momente, würdigst, was dir gelungen ist, "
        "und überlegst ganz ohne Druck, was du morgen ein wenig anders "
        "machen möchtest.",
        "Das dauert zusammen nur etwa sechs Minuten. Doch wer den Blick "
        "regelmäßig auf das Gute lenkt, trainiert ihn – ähnlich wie einen "
        "Muskel. Mit der Zeit fällt es dir leichter, Dankbarkeit, Ruhe und "
        "Zuversicht auch dann zu spüren, wenn ein Tag einmal fordernd ist.",
        "Du brauchst keine besonderen Vorkenntnisse. Du brauchst nur dich, "
        "einen Stift und ein paar ruhige Minuten. Fang einfach an – heute.",
    ]
    c.setFillColor(SOFT)
    for p in paras:
        for ln in wrap(c, p, "Serif", 11.5, w):
            txt(c, left, y, ln, "Serif", 11.5, SOFT, "l"); y -= 16
        y -= 8


def howto_page(bk):
    c = bk.c
    left, right, top, bottom = bk.new()
    w = right - left
    y = top - 6
    txt(c, left, y, "So funktioniert dein Ritual", "SerifB", 18, INK, "l")
    y -= 10
    c.setStrokeColor(ACCENT); c.setLineWidth(1.2); c.line(left, y, left + 60, y)
    y -= 28

    sun(c, left + 7, y - 2, 6.5, ACCENT)
    txt(c, left + 22, y - 5, "Morgens  ·  3 Minuten", "SansB", 12, INK, "l")
    y -= 22
    morning = [
        ("Dankbarkeit", "Notiere drei Dinge, für die du dankbar bist – gern auch ganz kleine."),
        ("Tagesfokus", "Was würde diesen Tag zu einem guten Tag machen?"),
        ("Affirmation", "Ein ermutigender Satz, der dich durch den Tag trägt."),
    ]
    for t, d in morning:
        txt(c, left + 8, y, "•  " + t + ": ", "SansB", 10.5, ACCENT, "l")
        txt(c, left + 8, y - 14, d, "Serif", 10.5, SOFT, "l")
        y -= 34

    y -= 6
    moon(c, left + 7, y - 2, 6.5, ACCENT)
    txt(c, left + 22, y - 5, "Abends  ·  3 Minuten", "SansB", 12, INK, "l")
    y -= 22
    evening = [
        ("Schöne Momente", "Welche drei Augenblicke haben dir heute gutgetan?"),
        ("Wachstum", "Was hast du heute gut gemacht oder Neues gelernt?"),
        ("Morgen besser", "Was möchtest du morgen ein wenig anders angehen?"),
    ]
    for t, d in evening:
        txt(c, left + 8, y, "•  " + t + ": ", "SansB", 10.5, ACCENT, "l")
        txt(c, left + 8, y - 14, d, "Serif", 10.5, SOFT, "l")
        y -= 34

    y -= 10
    band(c, left, y - 46, w, 40, SAND)
    txt(c, left + w/2, y - 22, "Tipp: Lege das Tagebuch sichtbar neben dein Bett.",
        "SerifI", 11, INK, "c")
    txt(c, left + w/2, y - 37, "Was wir sehen, tun wir eher.", "SerifI", 11, INK, "c")


def section_divider(bk, text, sub=""):
    c = bk.c
    left, right, top, bottom = bk.new()
    cx = (left + right) / 2
    c.setFillColor(SAND); c.rect(0, 0, PW, PH, stroke=0, fill=1)
    sun(c, cx, PH/2 + 60, 10, ACCENT)
    txt(c, cx, PH/2, text, "SerifB", 26, INK, "c")
    if sub:
        txt(c, cx, PH/2 - 30, sub, "SerifI", 13, SOFT, "c")
    c.setStrokeColor(GOLD); c.setLineWidth(1)
    c.line(cx - 40, PH/2 - 55, cx + 40, PH/2 - 55)


def notes_page(bk, heading="Notizen & Gedanken"):
    c = bk.c
    left, right, top, bottom = bk.new()
    w = right - left
    y = top
    txt(c, left, y, heading, "SerifB", 15, INK, "l")
    y -= 22
    writing_lines(c, left, w, y, 24, gap=(y - bottom - 10) / 24, color=LINEL)
    bk.page_number(left, right)


def blank_page(bk):
    bk.new()


def closing_page(bk):
    c = bk.c
    left, right, top, bottom = bk.new()
    w = right - left
    cx = (left + right) / 2
    c.setFillColor(SAND); c.rect(0, 0, PW, PH, stroke=0, fill=1)
    sun(c, cx, PH - 200, 11, ACCENT)
    txt(c, cx, PH - 250, "Herzlichen Glückwunsch!", "SerifB", 24, INK, "c")
    txt(c, cx, PH - 285, f"Du hast {DAYS} Tage lang innegehalten.", "Serif", 13, SOFT, "c")
    y = PH - 340
    for lbl in ["Wie hat sich dieses Ritual auf mich ausgewirkt?",
                "Was hat sich in mir verändert?",
                "Das nehme ich mir als Nächstes vor:"]:
        txt(c, left, y, lbl, "SansB", 10, ACCENT, "l")
        y -= 6
        y = writing_lines(c, left, w, y, 3, gap=22)
        y -= 22


# --------------------------------------------------------------------------
# AUFBAU
# --------------------------------------------------------------------------
def build_interior():
    bk = Book(INTERIOR)

    # -- Front-Matter --
    title_page(bk)          # 1 (recto)
    copyright_page(bk)      # 2 (verso)
    owner_page(bk)          # 3
    blank_page(bk)          # 4
    intro_page(bk)          # 5
    howto_page(bk)          # 6
    daily_page(bk, 1, IMPULSES[0], example=True)   # Beispielseite
    blank_page(bk)

    section_divider(bk, "Deine 180 Tage", "Ein Morgen- und Abendritual")
    blank_page(bk)

    # -- Tagesseiten + Wochenrückblick --
    week = 1
    for day in range(1, DAYS + 1):
        impulse = IMPULSES[(day - 1) % len(IMPULSES)]
        daily_page(bk, day, impulse)
        if day % WEEK_LEN == 0:
            weekly_page(bk, week)
            week += 1

    # -- Abschluss --
    closing_page(bk)
    for _ in range(4):
        notes_page(bk)

    # -- Auf gerade Seitenzahl auffüllen --
    if bk.page % 2 == 1:
        notes_page(bk)

    total = bk.page
    bk.save()
    return total


# --------------------------------------------------------------------------
# COVER
# --------------------------------------------------------------------------
def build_cover(page_count):
    BLEED = 0.125 * inch
    PAPER = 0.0025 * inch                    # Creme-Papier, pro Seite
    spine = page_count * PAPER
    cw = PW * 2 + spine + BLEED * 2
    ch = PH + BLEED * 2
    c = canvas.Canvas(COVER, pagesize=(cw, ch))

    c.setFillColor(SAND); c.rect(0, 0, cw, ch, stroke=0, fill=1)

    front_x0 = BLEED + PW + spine
    back_x0 = BLEED
    spine_x0 = BLEED + PW
    cyv = ch / 2

    # ---- FRONT ----
    fcx = front_x0 + PW / 2
    c.setFillColor(SANDD)
    c.rect(front_x0, ch - BLEED - 2.7 * inch, PW, 2.7 * inch, stroke=0, fill=1)
    sun(c, fcx, ch - BLEED - 1.0 * inch, 12, ACCENT)

    c.setFillColor(INK); c.setFont("SerifB", 34)
    for i, ln in enumerate(TITLE_DISP.split("\n")):
        c.drawCentredString(fcx, cyv + 70 - i * 40, ln)
    c.setStrokeColor(ACCENT); c.setLineWidth(1.2)
    c.line(fcx - 55, cyv + 20, fcx + 55, cyv + 20)
    c.setFillColor(SOFT); c.setFont("Serif", 13)
    for i, ln in enumerate(SUBTITLE.split("\n")):
        c.drawCentredString(fcx, cyv - 12 - i * 20, ln)
    c.setFillColor(ACCENT); c.setFont("SansB", 12)
    c.drawCentredString(fcx, BLEED + 1.1 * inch, f"{DAYS} TAGE  ·  MORGEN & ABEND")

    # ---- SPINE ----
    if spine > 0.35 * inch:
        c.saveState()
        c.translate(spine_x0 + spine / 2, ch / 2)
        c.rotate(90)
        c.setFillColor(INK); c.setFont("SerifB", 15)
        c.drawCentredString(0, -5, TITLE)
        c.restoreState()

    # ---- BACK ----
    bcx = back_x0 + PW / 2
    txt(c, bcx, ch - BLEED - 1.1 * inch, "Nimm dir sechs Minuten.", "SerifB", 17, INK, "c")
    txt(c, bcx, ch - BLEED - 1.35 * inch, "Für dich.", "SerifI", 15, ACCENT, "c")

    blurb = [
        "Drei Minuten am Morgen. Drei Minuten am Abend.",
        "Mehr braucht es nicht, um deinen Blick jeden Tag",
        "ein Stück weit auf das Gute zu lenken.",
        "",
        "Dieses Tagebuch begleitet dich 180 Tage lang mit",
        "einem einfachen, wohltuenden Ritual: Dankbarkeit,",
        "Fokus und Achtsamkeit – klar strukturiert und",
        "liebevoll gestaltet.",
        "",
        "•  Morgens: Dankbarkeit, Tagesfokus, Affirmation",
        "•  Abends:  schöne Momente, Wachstum, Ausblick",
        "•  Wöchentliche Rückblicke und Platz für Notizen",
        "",
        "Beginne heute – und schenke dir jeden Tag einen",
        "Moment nur für dich.",
    ]
    yy = ch - BLEED - 1.9 * inch
    c.setFont("Serif", 11); c.setFillColor(SOFT)
    for ln in blurb:
        if ln.startswith("•"):
            txt(c, back_x0 + 0.7 * inch, yy, ln, "Serif", 11, INK, "l")
        else:
            c.drawCentredString(bcx, yy, ln)
        yy -= 17

    # Platz für KDP-Barcode (weißes Feld unten rechts, 2" x 1.2")
    c.setFillColor(WHITE)
    c.rect(back_x0 + PW - BLEED - 2.0 * inch, BLEED + 0.35 * inch,
           2.0 * inch, 1.2 * inch, stroke=0, fill=1)

    c.showPage(); c.save()
    return spine, cw, ch


# --------------------------------------------------------------------------
if __name__ == "__main__":
    pages = build_interior()
    spine, cw, ch = build_cover(pages)
    print(f"Innenseiten  : {INTERIOR}")
    print(f"Seitenzahl   : {pages} (gerade: {pages % 2 == 0})")
    print(f"Cover        : {COVER}")
    print(f"Ruecken      : {spine/inch:.3f}\"  ({spine/inch*25.4:.1f} mm)")
    print(f"Cover-Groesse: {cw/inch:.3f}\" x {ch/inch:.3f}\"  "
          f"({cw/inch*25.4:.1f} x {ch/inch*25.4:.1f} mm)")
