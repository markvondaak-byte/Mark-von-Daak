#!/usr/bin/env python3
"""Baut das Werbevideo zu „Kopf schlägt Kalorien" (9:16, 1080 × 1920, 25 s).

    python3 kopf/build/build_video.py

Vorher müssen Innenteil und Umschlag gebaut sein — das Buch-Mockup wird aus
kopf/out/cover.png ausgeschnitten, das Hauptmotiv ist kopf/cover/titelbild.png.

Gesetzt wird Bild für Bild mit Pillow und direkt an ffmpeg gereicht. Kein
KI-Video: Die deutsche Schrift soll gestochen scharf und fehlerfrei sein, und
jede Aussage im Video muss im Buch stehen. Keine Kilogramm, keine Zeiträume
bis zu einem Ergebnis, keine Heilversprechen — dieselben Regeln wie für das
Amazon-Listing.

Das Video hat keine Tonspur. Musik aus der Bibliothek der jeweiligen
Plattform (Instagram, TikTok, YouTube) ist dort lizenziert; eine eigene Datei
müsste für Werbung eigens lizenziert sein.
"""

import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

WURZEL = Path(__file__).resolve().parents[2]
KOPF = WURZEL / "kopf"
AUS = KOPF / "out"

B, H = 1080, 1920
FPS = 30
DAUER = 25.0

SCHRIFT = "/usr/share/fonts/opentype/inter/InterDisplay-{}.otf"
NAVY_OBEN = (13, 24, 41)
NAVY_UNTEN = (27, 45, 70)
TEXT = (246, 242, 234)
LEISE = (184, 197, 212)
AKZENT = (247, 176, 62)


def schrift(schnitt, groesse):
    return ImageFont.truetype(SCHRIFT.format(schnitt), round(groesse))


# --- Bewegung ----------------------------------------------------------------
def klemmen(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def aus_kubisch(x):
    x = klemmen(x)
    return 1 - (1 - x) ** 3


def fenster(t, start, ende, ein=0.45, aus=0.35):
    """Deckkraft 0–1 für ein Element, das von start bis ende sichtbar ist."""
    if t < start or t > ende:
        return 0.0
    hinein = aus_kubisch((t - start) / ein)
    heraus = aus_kubisch((ende - t) / aus)
    return min(hinein, heraus)


# --- Bausteine, einmal vorberechnet ------------------------------------------
def verlauf(oben=NAVY_OBEN, unten=NAVY_UNTEN):
    spalte = Image.new("RGB", (1, H))
    for y in range(H):
        f = y / (H - 1)
        spalte.putpixel((0, y), tuple(round(a + (b - a) * f)
                                      for a, b in zip(oben, unten)))
    return spalte.resize((B, H))


def textbild(zeilen, groesse, schnitt="Black", farbe=TEXT, zeilenabstand=1.12,
             breite=B, sperrung=0):
    """Mehrzeiliger, zentrierter Text als RGBA-Sprite.

    Passt eine Zeile nicht in die Bildbreite (abzüglich 90 px Rand je Seite),
    wird die Schrift so weit verkleinert, dass sie passt.
    """
    f = schrift(schnitt, groesse)
    messen = ImageDraw.Draw(Image.new("L", (1, 1)))
    breiteste = max(messen.textlength(z, font=f) + sperrung * (len(z) - 1)
                    for z in zeilen)
    if breiteste > breite - 180:
        groesse = groesse * (breite - 180) / breiteste
        sperrung = sperrung * (breite - 180) / breiteste
        f = schrift(schnitt, groesse)
    hoehe = round(len(zeilen) * groesse * zeilenabstand + groesse * 0.4)
    bild = Image.new("RGBA", (breite, hoehe), (0, 0, 0, 0))
    z = ImageDraw.Draw(bild)
    for i, zeile in enumerate(zeilen):
        if sperrung:
            w = sum(z.textlength(ch, font=f) for ch in zeile) \
                + sperrung * (len(zeile) - 1)
            x = (breite - w) / 2
            for ch in zeile:
                z.text((x, i * groesse * zeilenabstand), ch, font=f, fill=farbe)
                x += z.textlength(ch, font=f) + sperrung
        else:
            w = z.textlength(zeile, font=f)
            z.text(((breite - w) / 2, i * groesse * zeilenabstand), zeile,
                   font=f, fill=farbe)
    return bild


def punktzeile(text, groesse=50):
    """Stichpunkt mit Bernstein-Punkt, linksbündig ab einem festen Rand."""
    f = schrift("SemiBold", groesse)
    bild = Image.new("RGBA", (B, round(groesse * 1.5)), (0, 0, 0, 0))
    z = ImageDraw.Draw(bild)
    r = groesse * 0.19
    links = 130
    z.ellipse((links, groesse * 0.62 - r, links + 2 * r, groesse * 0.62 + r),
              fill=AKZENT)
    z.text((links + 4 * r, 0), text, font=f, fill=TEXT)
    return bild


def buch_mockup(breite=600):
    """Vorderseite des Umschlags als stehendes Buch mit Rücken und Schatten."""
    umschlag = Image.open(AUS / "cover.png").convert("RGB")
    # Die Vorderseite ist das rechte Drittel; Anschnitt (3,175 mm) abschneiden.
    anschnitt = round(3.175 / 25.4 * 300)
    vorne_b = round(152.4 / 25.4 * 300)
    w, h = umschlag.size
    vorne = umschlag.crop((w - anschnitt - vorne_b, anschnitt,
                           w - anschnitt, h - anschnitt))
    hoehe = round(breite * vorne.height / vorne.width)
    vorne = vorne.resize((breite, hoehe), Image.LANCZOS)

    rand = 90
    bild = Image.new("RGBA", (breite + 2 * rand, hoehe + 2 * rand), (0, 0, 0, 0))
    schatten = Image.new("L", bild.size, 0)
    ImageDraw.Draw(schatten).rectangle(
        (rand + 18, rand + 28, rand + breite + 22, rand + hoehe + 30), fill=170)
    schatten = schatten.filter(ImageFilter.GaussianBlur(28))
    bild.paste((0, 0, 0, 255), (0, 0), schatten)

    bild.paste(vorne, (rand, rand))
    z = ImageDraw.Draw(bild, "RGBA")
    # Falz am Rücken: dunkler Streifen mit Lichtkante
    for i in range(22):
        alpha = round(110 * (1 - i / 22))
        z.line((rand + i, rand, rand + i, rand + hoehe), fill=(0, 0, 0, alpha))
    z.line((rand + 24, rand, rand + 24, rand + hoehe),
           fill=(255, 255, 255, 40), width=2)
    # Glanz über die Fläche
    glanz = Image.new("L", bild.size, 0)
    ImageDraw.Draw(glanz).polygon(
        [(rand + breite * 0.55, rand), (rand + breite * 0.80, rand),
         (rand + breite * 0.35, rand + hoehe), (rand + breite * 0.10, rand + hoehe)],
        fill=26)
    glanz = glanz.filter(ImageFilter.GaussianBlur(30))
    bild.paste((255, 255, 255, 255), (0, 0), glanz)
    return bild


def lichtschein(radius=620):
    """Weicher, warmer Lichtfleck, der langsam durch den Hintergrund wandert."""
    maske = Image.new("L", (2 * radius, 2 * radius), 0)
    ImageDraw.Draw(maske).ellipse((radius * 0.35, radius * 0.35,
                                   radius * 1.65, radius * 1.65), fill=255)
    maske = maske.filter(ImageFilter.GaussianBlur(radius * 0.28))
    licht = Image.new("RGBA", maske.size, (120, 92, 58, 0))
    licht.putalpha(maske)
    return licht


def titelmotiv():
    """Gehirn-Donut, so skaliert, dass er auch mit Zoom das Bild füllt."""
    foto = Image.open(KOPF / "cover" / "titelbild.png").convert("RGB")
    faktor = max(B / foto.width, H / foto.height) * 1.12
    return foto.resize((round(foto.width * faktor), round(foto.height * faktor)),
                       Image.LANCZOS)


# --- Zusammensetzen ----------------------------------------------------------
def einsetzen(bild, sprite, x, y, deckung):
    if deckung <= 0:
        return
    if deckung < 1:
        alpha = sprite.split()[3].point(lambda v: round(v * deckung))
        sprite = sprite.copy()
        sprite.putalpha(alpha)
    bild.alpha_composite(sprite, (round(x), round(y)))


def einblenden(bild, sprite, y, t, start, ende, hub=60):
    """Zentriert einsetzen, beim Erscheinen von unten nachrücken."""
    d = fenster(t, start, ende)
    if d <= 0:
        return
    versatz = (1 - aus_kubisch((t - start) / 0.6)) * hub
    einsetzen(bild, sprite, (B - sprite.width) / 2, y + versatz, d)


class Video:
    def __init__(self):
        self.grund = verlauf().convert("RGBA")
        self.licht = lichtschein()
        self.motiv = titelmotiv()
        self.buch = buch_mockup(600)
        self.buch_klein = self.buch.resize(
            (round(self.buch.width * 0.82), round(self.buch.height * 0.82)),
            Image.LANCZOS)

        # Szene 1 — Hook
        self.s1a = textbild(["Du weißt, was du", "essen solltest."], 112)
        self.s1b = textbild(["Warum tust du", "es nicht?"], 132, farbe=AKZENT)
        # Szene 2 — Wiedererkennen
        self.s2kopf = textbild(["KENNST DU DAS?"], 46, "SemiBold", AKZENT,
                               sperrung=8)
        self.s2 = [textbild([z], 57, "ExtraBold") for z in (
            "Abends um neun auf dem Sofa.",
            "Nach einem stressigen Tag.",
            "Montags nach dem Wochenende.")]
        # Szene 3 — Wendung
        self.s3a = textbild(["Es liegt nicht", "am Plan."], 118, farbe=LEISE)
        self.s3b = textbild(["Es liegt", "im Kopf."], 160, farbe=AKZENT)
        # Szene 4 — Inhalte
        self.s4kopf = textbild(["WAS DU IN DIESEM BUCH LERNST"], 40, "SemiBold",
                               AKZENT, sperrung=6)
        self.s4 = [punktzeile(z) for z in (
            "Motivation, die trägt",
            "Heißhunger verstehen",
            "Wenn-Dann-Pläne statt Willenskraft",
            "Ausrutscher ohne Rückfall")]
        # Szene 5 — Buch
        self.s5a = textbild(["Kein Ernährungsplan.", "Kein Versprechen über Kilos."],
                            60, "ExtraBold")
        self.s5b = textbild(["Dafür das, was jeden Plan", "durchhaltbar macht."],
                            54, "Medium", LEISE)
        # Szene 6 — Abschluss
        self.s6a = textbild(["JETZT ERHÄLTLICH"], 50, "SemiBold", AKZENT,
                            sperrung=9)
        self.s6b = textbild(["Taschenbuch · Hardcover · E-Book"], 54, "ExtraBold")
        self.s6c = textbild(["bei Amazon"], 54, "Medium", LEISE)
        self.s6d = textbild(["MARK VON DAAK"], 44, "SemiBold", TEXT, sperrung=10)

    def bild(self, t):
        bild = self.grund.copy()

        # Wandernder Lichtschein hinter allen Textszenen
        lx = B / 2 + math.sin(t * 0.32) * 260 - self.licht.width / 2
        ly = H * 0.36 + math.cos(t * 0.27) * 220 - self.licht.height / 2
        einsetzen(bild, self.licht, lx, ly, 0.42 + 0.12 * math.sin(t * 0.9))

        # Szene 4: Hauptmotiv mit langsamem Zoom und weicher Blende
        d4 = fenster(t, 9.7, 16.6, ein=0.8, aus=0.6)
        if d4 > 0:
            zoom = 1.0 + 0.06 * klemmen((t - 9.7) / 6.9)
            m = self.motiv.resize((round(self.motiv.width * zoom),
                                   round(self.motiv.height * zoom)),
                                  Image.BILINEAR)
            x = (B - m.width) / 2
            y = -(m.height - H) * 0.15
            ebene = Image.new("RGBA", (B, H), (0, 0, 0, 0))
            ebene.paste(m, (round(x), round(y)))
            einsetzen(bild, ebene, 0, 0, d4)

        # Szene 1
        einblenden(bild, self.s1a, 640, t, 0.2, 3.1)
        einblenden(bild, self.s1b, 960, t, 1.3, 3.1)

        # Szene 2
        einblenden(bild, self.s2kopf, 620, t, 3.3, 6.8, hub=30)
        for i, sprite in enumerate(self.s2):
            einblenden(bild, sprite, 760 + i * 150, t, 3.6 + i * 0.9, 6.8)

        # Szene 3
        einblenden(bild, self.s3a, 660, t, 7.0, 9.8)
        einblenden(bild, self.s3b, 960, t, 8.1, 9.8, hub=80)

        # Szene 4: Texte über dem dunklen unteren Bildteil
        einblenden(bild, self.s4kopf, 1180, t, 10.8, 16.4, hub=30)
        for i, sprite in enumerate(self.s4):
            d = fenster(t, 11.3 + i * 0.8, 16.4)
            if d > 0:
                schub = (1 - aus_kubisch((t - 11.3 - i * 0.8) / 0.6)) * -70
                einsetzen(bild, sprite, schub, 1280 + i * 105, d)

        # Szene 5: Buch schwebt ein
        d5 = fenster(t, 16.6, 21.0, ein=0.7, aus=0.4)
        if d5 > 0:
            auf = aus_kubisch((t - 16.6) / 1.0)
            schweben = math.sin((t - 16.6) * 1.6) * 8
            y = 230 + (1 - auf) * 260 + schweben
            einsetzen(bild, self.buch, (B - self.buch.width) / 2, y, d5)
        einblenden(bild, self.s5a, 1440, t, 17.6, 21.0)
        einblenden(bild, self.s5b, 1610, t, 18.6, 21.0)

        # Szene 6: Abschluss
        d6 = fenster(t, 21.0, DAUER + 1, ein=0.6)
        if d6 > 0:
            schweben = math.sin((t - 21.0) * 1.6) * 6
            einsetzen(bild, self.buch_klein, (B - self.buch_klein.width) / 2,
                      150 + schweben, d6)
        einblenden(bild, self.s6a, 1330, t, 21.4, DAUER + 1, hub=30)
        einblenden(bild, self.s6b, 1425, t, 21.8, DAUER + 1)
        einblenden(bild, self.s6c, 1510, t, 22.2, DAUER + 1)
        einblenden(bild, self.s6d, 1680, t, 22.8, DAUER + 1, hub=30)

        # Abblende am Ende
        if t > DAUER - 0.5:
            schwarz = Image.new("RGBA", (B, H), (0, 0, 0, 255))
            einsetzen(bild, schwarz, 0, 0, (t - (DAUER - 0.5)) / 0.5)
        return bild.convert("RGB")


def main():
    for pflicht in (AUS / "cover.png", KOPF / "cover" / "titelbild.png"):
        if not pflicht.exists():
            raise SystemExit(f"{pflicht.relative_to(WURZEL)} fehlt — erst "
                             "build_kopf.py und build_cover.py laufen lassen.")
    ziel = AUS / "werbevideo-9x16.mp4"
    video = Video()
    befehl = ["ffmpeg", "-y", "-loglevel", "error",
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{B}x{H}",
              "-r", str(FPS), "-i", "-",
              "-c:v", "libx264", "-preset", "slow", "-crf", "18",
              "-pix_fmt", "yuv420p", "-movflags", "+faststart",
              str(ziel)]
    prozess = subprocess.Popen(befehl, stdin=subprocess.PIPE)
    anzahl = round(DAUER * FPS)
    for n in range(anzahl):
        prozess.stdin.write(video.bild(n / FPS).tobytes())
    prozess.stdin.close()
    if prozess.wait() != 0:
        raise SystemExit("ffmpeg ist fehlgeschlagen.")

    # Standbilder zur Kontrolle, je eines pro Szene
    for sekunde in (2.6, 6.2, 9.2, 15.2, 20.2, 24.0):
        video.bild(sekunde).resize((B // 3, H // 3)).save(
            AUS / f"werbevideo-standbild-{sekunde:04.1f}s.png")
    print(f"{anzahl} Bilder, {DAUER:.0f} s, {B} x {H}, {FPS} fps")
    print(f"  → {ziel.relative_to(WURZEL)}  "
          f"({ziel.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
