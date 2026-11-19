#!/usr/bin/env python3
"""Baut den Trailer zu „Die Dopamin-Lüge" (9:16, 1080 × 1920, 18 s, mit Musik).

    python3 dopamin/build/build_trailer.py

Vorher muss der Umschlag gebaut sein (dopamin/out/cover.png) — das
Buch-Mockup wird aus der Vorderseite ausgeschnitten. Das Hauptmotiv ist
dopamin/cover/titelbild.png (Kopf im Profil mit leuchtenden Synapsen). Die
Musik rechnet trailer_musik.py; sie ist selbst synthetisiert und damit frei
von fremden Rechten.

Bild für Bild mit Pillow gesetzt und mit der Musik an ffmpeg gereicht.
Schnitte, Lichtblitze und Texteinsätze liegen auf dem Takt der Musik
(120 BPM, ein Takt = 2 s). Alle Sätze stammen aus dem Klappentext und stehen
so im Buch; Anrede „Sie" wie im Buch.

  0–4 s    Dunkel. Ein Benachrichtigungston, das Telefon leuchtet auf, der
           Feed läuft. „23:20 Uhr. Sie greifen zum Telefon."
  4–8 s    „40 Minuten später. Nichts davon hat Spaß gemacht. Aufhören
           konnten Sie trotzdem nicht." — Anlauf zum Einschlag.
  8–12 s   Einschlag. Das Titelmotiv, pulsierend im Takt: „Dopamin macht
           kein Glück. Es macht Verlangen."
  12–18 s  Zweiter Einschlag. Das Buch mit Lichtschein und Spiegelung,
           „Jetzt erhältlich", Ausklang.
"""

import importlib.util
import math
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

WURZEL = Path(__file__).resolve().parents[2]
BAND = WURZEL / "dopamin"
AUS = BAND / "out"


def _laden(name, pfad):
    spec = importlib.util.spec_from_file_location(name, pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


NV = _laden("narzisst_video", WURZEL / "narzisst" / "build" / "build_video.py")
MUSIK = _laden("trailer_musik", BAND / "build" / "trailer_musik.py")
KV = NV.KV
B, H, FPS = KV.B, KV.H, KV.FPS
DAUER = MUSIK.DAUER
SCHLAG = MUSIK.SCHLAG
EINSCHLAEGE = MUSIK.EINSCHLAEGE

# Farbwelt des Umschlags: Indigo, Violett, kaltes Bildschirmblau.
TEXT = (242, 241, 248)
LEISE = (172, 168, 204)
AKZENT = (168, 158, 255)
GRUND_OBEN = (24, 22, 54)
GRUND_UNTEN = (8, 7, 22)
BILDSCHIRM = (110, 160, 255)
BLITZ = (226, 220, 255)

KV.AUS = AUS
KV.AKZENT = AKZENT
KV.TEXT = TEXT

fenster, aus_kubisch, klemmen = KV.fenster, KV.aus_kubisch, KV.klemmen
einsetzen = KV.einsetzen
schrift = KV.schrift


# --- Kinetische Schrift ------------------------------------------------------
class Zeile:
    """Eine Textzeile, deren Wörter nacheinander einfliegen."""

    def __init__(self, text, groesse, schnitt="Black", farbe=TEXT):
        f = schrift(schnitt, groesse)
        messen = ImageDraw.Draw(Image.new("L", (1, 1)))
        luecke = messen.textlength(" ", font=f)
        woerter = text.split()
        breiten = [messen.textlength(w, font=f) for w in woerter]
        gesamt = sum(breiten) + luecke * (len(woerter) - 1)
        faktor = min(1.0, (B - 160) / gesamt)
        if faktor < 1:
            f = schrift(schnitt, groesse * faktor)
            luecke *= faktor
            breiten = [messen.textlength(w, font=f) for w in woerter]
            gesamt = sum(breiten) + luecke * (len(woerter) - 1)
        self.hoehe = round(f.size * 1.25)
        self.woerter = []
        x = (B - gesamt) / 2
        for w, br in zip(woerter, breiten):
            sprite = Image.new("RGBA", (round(br) + 20, self.hoehe + 20),
                               (0, 0, 0, 0))
            ImageDraw.Draw(sprite).text((10, 6), w, font=f, fill=farbe)
            self.woerter.append((sprite, x - 10))
            x += br + luecke

    def zeichnen(self, bild, y, t, start, ende, abstand=0.085):
        for i, (sprite, x) in enumerate(self.woerter):
            a = start + i * abstand
            d = fenster(t, a, ende, ein=0.3, aus=0.3)
            if d <= 0:
                continue
            p = aus_kubisch((t - a) / 0.45)
            skal = 0.82 + 0.18 * p
            s = sprite if skal >= 0.999 else sprite.resize(
                (max(1, round(sprite.width * skal)),
                 max(1, round(sprite.height * skal))), Image.BILINEAR)
            dx = (sprite.width - s.width) / 2
            dy = (sprite.height - s.height) / 2 + (1 - p) * 34
            einsetzen(bild, s, x + dx, y + dy, d)


def gesperrt(text, groesse, schnitt, farbe, sperrung):
    return KV.textbild([text], groesse, schnitt, farbe, sperrung=sperrung)


# --- Bausteine ---------------------------------------------------------------
def glanzpunkt(radius, farbe):
    groesse = radius * 6
    maske = Image.new("L", (groesse, groesse), 0)
    z = ImageDraw.Draw(maske)
    m = groesse / 2
    z.ellipse((m - radius * 2.6, m - radius * 2.6, m + radius * 2.6,
               m + radius * 2.6), fill=70)
    maske = maske.filter(ImageFilter.GaussianBlur(radius * 1.2))
    ImageDraw.Draw(maske).ellipse((m - radius, m - radius, m + radius,
                                   m + radius), fill=255)
    punkt = Image.new("RGBA", (groesse, groesse), farbe + (0,))
    punkt.putalpha(maske)
    return punkt


class Teilchen:
    """Schwebende Lichtpunkte wie Synapsen — fest verteilt, jeder Lauf gleich."""

    def __init__(self, anzahl=46):
        zufall = random.Random(2320)
        self.punkte = []
        for _ in range(anzahl):
            r = zufall.choice((3, 4, 5, 7))
            farbe = zufall.choice((AKZENT, BILDSCHIRM, (255, 196, 140)))
            self.punkte.append({
                "sprite": glanzpunkt(r, farbe),
                "x": zufall.uniform(0, B), "y": zufall.uniform(0, H),
                "vx": zufall.uniform(-12, 12), "vy": zufall.uniform(-38, -10),
                "phase": zufall.uniform(0, 6.3), "tempo": zufall.uniform(1, 3),
            })

    def zeichnen(self, bild, t, deckung, puls=0.0):
        if deckung <= 0:
            return
        for p in self.punkte:
            x = (p["x"] + p["vx"] * t) % (B + 80) - 40
            y = (p["y"] + p["vy"] * t) % (H + 80) - 40
            funkeln = 0.45 + 0.4 * math.sin(p["phase"] + t * p["tempo"])
            s = p["sprite"]
            einsetzen(bild, s, x - s.width / 2, y - s.height / 2,
                      min(1, deckung * (funkeln + puls)))


def lichtfleck(radius, farbe, staerke):
    maske = Image.new("L", (2 * radius, 2 * radius), 0)
    ImageDraw.Draw(maske).ellipse((radius * 0.3, radius * 0.3, radius * 1.7,
                                   radius * 1.7), fill=round(255 * staerke))
    maske = maske.filter(ImageFilter.GaussianBlur(radius * 0.32))
    licht = Image.new("RGBA", maske.size, farbe + (0,))
    licht.putalpha(maske)
    return licht


class Telefon:
    """Telefon mit laufendem Feed. Das Gehäuse wird einmal gezeichnet, der
    Bildschirminhalt je Bild — die Kacheln scrollen endlos nach oben."""

    B, H = 360, 720

    def __init__(self):
        b, h = self.B, self.H
        self.gehaeuse = Image.new("RGBA", (b, h), (0, 0, 0, 0))
        z = ImageDraw.Draw(self.gehaeuse)
        z.rounded_rectangle((0, 0, b - 1, h - 1), radius=58,
                            fill=(16, 16, 26, 255))
        z.rounded_rectangle((2, 2, b - 3, h - 3), radius=56,
                            outline=(92, 96, 130, 255), width=2)
        self.schirm_kasten = (16, 16, b - 16, h - 16)
        self.maske = Image.new("L", (b, h), 0)
        ImageDraw.Draw(self.maske).rounded_rectangle(self.schirm_kasten,
                                                     radius=44, fill=255)
        self.schein = lichtfleck(560, BILDSCHIRM, 0.75)
        zufall = random.Random(40)
        self.kacheln = [(zufall.choice((150, 210, 260)),
                         zufall.choice(((60, 92, 170), (86, 70, 170),
                                        (46, 110, 160))))
                        for _ in range(12)]

    def bild(self, t, hell):
        b, h = self.B, self.H
        schirm = Image.new("RGB", (b, h), (22, 30, 60))
        z = ImageDraw.Draw(schirm)
        gesamt = sum(k[0] + 18 for k in self.kacheln)
        y = 30 - (t * 210) % gesamt
        for _ in range(2):
            for hoehe, farbe in self.kacheln:
                if -hoehe < y < h:
                    z.rounded_rectangle((34, y, b - 34, y + hoehe), radius=18,
                                        fill=farbe)
                    z.ellipse((50, y + 16, 86, y + 52), fill=(200, 210, 255))
                    z.rounded_rectangle((98, y + 24, b - 120, y + 42),
                                        radius=8, fill=(150, 170, 230))
                y += hoehe + 18
        # Statusleiste und Uhrzeit
        z.rectangle((0, 0, b, 64), fill=(14, 18, 40))
        # 40 Minuten später zeigt auch das Telefon die neue Uhrzeit
        uhrzeit = "23:20" if t < 4.0 else "00:00"
        z.text((b / 2 - 40, 26), uhrzeit, font=schrift("SemiBold", 28),
               fill=(230, 234, 255))
        schirm = Image.blend(Image.new("RGB", (b, h)), schirm, hell)
        telefon = self.gehaeuse.copy()
        telefon.paste(schirm, (0, 0), self.maske)
        return telefon


def titelmotiv():
    foto = Image.open(BAND / "cover" / "titelbild.png").convert("RGB")
    faktor = max(B / foto.width, H / foto.height) * 1.02
    return foto.resize((round(foto.width * faktor), round(foto.height * faktor)),
                       Image.LANCZOS)


def fahrt(foto, t, start, dauer):
    f = klemmen((t - start) / dauer)
    zoom = 1.0 + 0.10 * f
    fb, fh = B / zoom, H / zoom
    mx = foto.width * (0.47 + 0.07 * f)
    my = foto.height * 0.46
    x0 = min(max(mx - fb / 2, 0), foto.width - fb)
    y0 = min(max(my - fh / 2, 0), foto.height - fh)
    return foto.resize((B, H), Image.BILINEAR, box=(x0, y0, x0 + fb, y0 + fh))


def unten_dunkel(ab=0.5, staerke=235):
    """Schwarzer Verlauf über die untere Bildhälfte — Grund für die Schrift."""
    maske = Image.new("L", (1, H), 0)
    for y in range(H):
        anteil = klemmen((y / H - ab) / (1 - ab))
        maske.putpixel((0, y), round(staerke * anteil ** 1.2))
    schwarz = Image.new("RGBA", (B, H), GRUND_UNTEN + (255,))
    schwarz.putalpha(maske.resize((B, H)))
    return schwarz


def spiegelung(buch, hoehe=170):
    """Spiegelbild des Buchs auf glänzendem Boden, nach unten ausgeblendet."""
    unten = buch.crop((0, buch.height - 90 - hoehe, buch.width,
                       buch.height - 90)).transpose(Image.FLIP_TOP_BOTTOM)
    alpha = unten.split()[3]
    verlauf = Image.new("L", (1, hoehe), 0)
    for y in range(hoehe):
        verlauf.putpixel((0, y), round(70 * (1 - y / hoehe) ** 2))
    alpha = Image.composite(alpha, Image.new("L", alpha.size, 0),
                            verlauf.resize(alpha.size))
    unten.putalpha(alpha)
    return unten.filter(ImageFilter.GaussianBlur(2))


# --- Takt ---------------------------------------------------------------------
def nach_einschlag(t):
    """0–1: wie stark der letzte Einschlag noch nachwirkt."""
    werte = [math.exp(-(t - e) / 0.16) for e in EINSCHLAEGE if t >= e]
    return max(werte, default=0.0)


def schlagpuls(t, ab, bis):
    """Kurzer Puls auf jedem Schlag zwischen `ab` und `bis`."""
    if not ab <= t < bis:
        return 0.0
    return math.exp(-((t - ab) % SCHLAG) / 0.09)


# --- Trailer ------------------------------------------------------------------
class Trailer:
    def __init__(self):
        self.grund = KV.verlauf(GRUND_OBEN, GRUND_UNTEN).convert("RGBA")
        self.teilchen = Teilchen()
        self.telefon = Telefon()
        self.motiv = titelmotiv()
        self.dunkel = unten_dunkel()
        self.vignette = NV.vignette()
        self.korn = NV.filmkorn(staerke=12)
        self.buch = KV.buch_mockup(540)
        self.spiegel = spiegelung(self.buch)
        self.buchschein = lichtfleck(620, AKZENT, 0.55)

        self.s1a = Zeile("23:20 Uhr.", 168, farbe=AKZENT)
        self.s1b = Zeile("Sie greifen zum Telefon.", 82)
        self.s2a = Zeile("40 Minuten später.", 74, "SemiBold", LEISE)
        self.s2b = Zeile("Nichts davon", 92)
        self.s2c = Zeile("hat Spaß gemacht.", 92)
        self.s2d = Zeile("Aufhören konnten Sie", 92, farbe=AKZENT)
        self.s2e = Zeile("trotzdem nicht.", 92, farbe=AKZENT)
        self.s3a = Zeile("Dopamin macht", 116)
        self.s3b = Zeile("kein Glück.", 116)
        self.s3c = Zeile("Es macht Verlangen.", 112, farbe=AKZENT)
        self.s4a = Zeile("Die Unterscheidung, die alles verändert.", 50,
                         "Medium", LEISE)
        self.s4b = gesperrt("JETZT ERHÄLTLICH", 46, "SemiBold", AKZENT, 9)
        self.s4c = gesperrt("Taschenbuch · Hardcover · E-Book", 52,
                            "ExtraBold", TEXT, 0)
        self.s4d = gesperrt("bei Amazon", 50, "Medium", LEISE, 0)
        self.s4e = gesperrt("MARK VON DAAK", 40, "SemiBold", TEXT, 10)

    def bild(self, t):
        bild = self.grund.copy()
        puls = schlagpuls(t, 8.0, 16.0)

        # 0–8 s: Telefon im dunklen Raum; es leuchtet mit dem Ping auf
        d_tel = fenster(t, 0.42, 8.15, ein=0.25, aus=0.2)
        if d_tel > 0:
            flackern = 0.9 + 0.1 * math.sin(t * 9.1) * math.sin(t * 2.3)
            s = self.telefon.schein
            einsetzen(bild, s, (B - s.width) / 2, 1290 - s.height / 2,
                      d_tel * flackern * (0.7 if t > 4 else 1.0))
            schweben = math.sin(t * 1.2) * 8
            zoom = 1.0 + 0.05 * klemmen(t / 8)
            tel = self.telefon.bild(t, hell=d_tel)
            if zoom != 1:
                tel = tel.resize((round(tel.width * zoom),
                                  round(tel.height * zoom)), Image.BILINEAR)
            einsetzen(bild, tel, (B - tel.width) / 2, 1000 + schweben, 1.0)
        self.teilchen.zeichnen(bild, t, fenster(t, 2.0, 8.2, ein=1.5) * 0.6)

        # 8–12 s: Titelmotiv, pulsiert im Takt
        d_motiv = fenster(t, 8.0, 12.05, ein=0.02, aus=0.05)
        if d_motiv > 0:
            m = fahrt(self.motiv, t, 8.0, 4.0).convert("RGBA")
            einsetzen(bild, m, 0, 0, d_motiv)
            einsetzen(bild, Image.new("RGBA", (B, H), AKZENT + (255,)), 0, 0,
                      d_motiv * puls * 0.07)
            einsetzen(bild, self.dunkel, 0, 0, d_motiv)
            einsetzen(bild, self.vignette, 0, 0, d_motiv * 0.8)

        # 12–18 s: Buch mit Lichtschein, Spiegelung und Teilchen
        d4 = fenster(t, 12.0, DAUER + 1, ein=0.05)
        if d4 > 0:
            self.teilchen.zeichnen(bild, t, d4 * 0.8, puls * 0.3)
            schein = self.buchschein
            einsetzen(bild, schein, (B - schein.width) / 2,
                      640 - schein.height / 2, d4 * (0.75 + 0.25 * puls))
            auf = aus_kubisch((t - 12.0) / 1.1)
            schweben = math.sin((t - 12.0) * 1.4) * 6
            y = 120 + (1 - auf) * 160 + schweben
            x = (B - self.buch.width) / 2
            einsetzen(bild, self.buch, x, y, d4)
            einsetzen(bild, self.spiegel, x, y + self.buch.height - 90 + 4,
                      d4 * auf)

        # Schrift
        self.s1a.zeichnen(bild, 470, t, 0.55, 3.85)
        self.s1b.zeichnen(bild, 690, t, 1.5, 3.85)
        self.s2a.zeichnen(bild, 330, t, 4.05, 7.85)
        self.s2b.zeichnen(bild, 470, t, 4.7, 7.85)
        self.s2c.zeichnen(bild, 580, t, 4.95, 7.85)
        self.s2d.zeichnen(bild, 740, t, 6.0, 7.85)
        self.s2e.zeichnen(bild, 850, t, 6.3, 7.85)
        self.s3a.zeichnen(bild, 1150, t, 8.05, 11.9, abstand=0.12)
        self.s3b.zeichnen(bild, 1290, t, 8.55, 11.9, abstand=0.12)
        self.s3c.zeichnen(bild, 1500, t, 10.0, 11.9, abstand=0.14)
        self.s4a.zeichnen(bild, 1270, t, 13.0, DAUER + 1, abstand=0.05)
        for sprite, y, start in ((self.s4b, 1380, 13.6), (self.s4c, 1460, 14.0),
                                 (self.s4d, 1540, 14.3), (self.s4e, 1680, 14.8)):
            KV.einblenden(bild, sprite, y, t, start, DAUER + 1, hub=26)

        ergebnis = bild.convert("RGB")

        # Einschlag: Lichtblitz und ein kurzer Zoom-Stoß des ganzen Bildes
        stoss = nach_einschlag(t)
        if stoss > 0.01:
            zoom = 1 + 0.045 * stoss
            fb, fh = B / zoom, H / zoom
            ergebnis = ergebnis.resize((B, H), Image.BILINEAR,
                                       box=((B - fb) / 2, (H - fh) / 2,
                                            (B + fb) / 2, (H + fh) / 2))
            ergebnis = Image.blend(ergebnis, Image.new("RGB", (B, H), BLITZ),
                                   0.6 * stoss)

        ergebnis = Image.blend(ergebnis,
                               self.korn[int(t * 12) % len(self.korn)], 0.025)
        if t > DAUER - 1.0:
            ergebnis = Image.blend(ergebnis, Image.new("RGB", (B, H)),
                                   klemmen((t - (DAUER - 1.0)) / 1.0))
        return ergebnis


def main():
    for pflicht in (AUS / "cover.png", BAND / "cover" / "titelbild.png"):
        if not pflicht.exists():
            raise SystemExit(f"{pflicht.relative_to(WURZEL)} fehlt — erst "
                             "den Umschlag bauen.")
    musik = MUSIK.bauen(AUS / "trailer-musik.wav")
    ziel = AUS / "trailer-9x16.mp4"
    trailer = Trailer()
    # Lautheit für Social Media: rund −14 LUFS
    befehl = ["ffmpeg", "-y", "-loglevel", "error",
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{B}x{H}",
              "-r", str(FPS), "-i", "-", "-i", str(musik),
              "-map", "0:v", "-map", "1:a",
              "-c:v", "libx264", "-preset", "slow", "-crf", "17",
              "-pix_fmt", "yuv420p",
              "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
              "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
              "-shortest", "-movflags", "+faststart", str(ziel)]
    prozess = subprocess.Popen(befehl, stdin=subprocess.PIPE)
    anzahl = round(DAUER * FPS)
    for n in range(anzahl):
        prozess.stdin.write(trailer.bild(n / FPS).tobytes())
    prozess.stdin.close()
    if prozess.wait() != 0:
        raise SystemExit("ffmpeg ist fehlgeschlagen.")
    for sekunde in (3.4, 7.4, 8.1, 11.2, 16.5):
        trailer.bild(sekunde).resize((B // 3, H // 3)).save(
            AUS / f"trailer-standbild-{sekunde:04.1f}s.png")
    print(f"{anzahl} Bilder, {DAUER:.0f} s, {B} x {H}, {FPS} fps, mit Musik")
    print(f"  → {ziel.relative_to(WURZEL)}  "
          f"({ziel.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
