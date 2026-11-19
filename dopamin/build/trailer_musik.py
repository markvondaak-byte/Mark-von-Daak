#!/usr/bin/env python3
"""Musik zum Trailer von „Die Dopamin-Lüge" — selbst synthetisiert.

    python3 dopamin/build/trailer_musik.py      # schreibt out/trailer-musik.wav

Warum synthetisiert und nicht aus einer Bibliothek: Für Werbung braucht jede
fremde Aufnahme eine Lizenz, die ausdrücklich Werbung abdeckt. Diese Spur ist
aus Sinusschwingungen und Rauschen gerechnet und gehört damit dem Autor.

Aufbau, 120 BPM (ein Takt = 2 s), d-Moll — passend zu den Szenen des Videos:

  0–8 s    Dunkler Flächenklang, ein Herzschlag je Takt, ein Benachrichtigungs-
           ton, sobald das Telefon aufleuchtet. Ab 4 s ein leises Arpeggio.
  8 s      Einschlag. Vierviertel-Puls, Bass, Hi-Hats: „Es macht Verlangen."
  12 s     Zweiter Einschlag, volle Besetzung für das Buch.
  16–18 s  Auflösung auf d-Moll, Ausklang.

Nur numpy; der Hall ist eine Faltung mit abklingendem Rauschen.
"""

import wave
from pathlib import Path

import numpy as np

SR = 44100
BPM = 120
SCHLAG = 60 / BPM
DAUER = 18.0
N = int(SR * DAUER)

# Takt (2 s) → Akkord als MIDI-Noten. Dm · Dm · B · Gm · Dm · B · F · C · Dm
AKKORDE = [
    (50, 53, 57, 62), (50, 53, 57, 62), (46, 50, 53, 58), (43, 46, 50, 55),
    (50, 53, 57, 62), (46, 50, 53, 58), (41, 45, 48, 53), (48, 52, 55, 60),
    (50, 53, 57, 64),
]
EINSCHLAEGE = (8.0, 12.0)

zufall = np.random.default_rng(2320)


def tiefpass(signal, breite):
    """Gleitender Mittelwert — einfacher Tiefpass, nimmt Rauschen die Schärfe."""
    return np.convolve(signal, np.ones(breite) / breite, mode="same")


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def zeitachse(dauer):
    return np.arange(int(SR * dauer)) / SR


def addieren(spur, signal, start):
    a = int(start * SR)
    if a >= len(spur):
        return
    e = min(len(spur), a + len(signal))
    spur[a:e] += signal[:e - a]


def huelle(n, ein, aus):
    h = np.ones(n)
    a, r = int(ein * SR), int(aus * SR)
    if a:
        h[:a] = np.linspace(0, 1, a)
    if r:
        h[-r:] *= np.linspace(1, 0, r)
    return h


# --- Instrumente -------------------------------------------------------------
def flaeche(noten, dauer, hell):
    """Weicher Synth-Teppich: je Ton zwei leicht verstimmte Stimmen mit
    Obertönen; `hell` (0–1) bestimmt, wie viele Obertöne mitklingen."""
    t = zeitachse(dauer)
    s = np.zeros_like(t)
    obertoene = 3 + int(hell * 5)
    for m in noten:
        for verstimmung in (-0.0018, 0.0018):
            f = hz(m) * (1 + verstimmung)
            for n in range(1, obertoene + 1):
                s += np.sin(2 * np.pi * f * n * t + n) / n ** 1.7
    s *= huelle(len(t), 0.7, 0.9) / (len(noten) * 4)
    # langsames Atmen der Lautstärke
    return s * (0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * t))


def pluck(midi, dauer=0.32):
    t = zeitachse(dauer)
    f = hz(midi)
    s = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)
         + 0.12 * np.sin(6 * np.pi * f * t))
    return s * np.exp(-t / 0.09) * huelle(len(t), 0.003, 0.02)


def kick(staerke=1.0):
    t = zeitachse(0.45)
    frequenz = 45 + 85 * np.exp(-t / 0.035)
    phase = 2 * np.pi * np.cumsum(frequenz) / SR
    s = np.sin(phase) * np.exp(-t / 0.16)
    s[:200] += tiefpass(zufall.normal(0, 0.08, 200), 6) * np.linspace(1, 0, 200)
    return s * staerke


def herzschlag():
    s = np.zeros(int(SR * 0.6))
    addieren(s, kick(0.9), 0)
    addieren(s, kick(0.55), 0.24)
    return s


def hihat():
    t = zeitachse(0.06)
    rauschen = np.diff(zufall.normal(0, 1, len(t) + 1))   # Hochpass light
    return tiefpass(rauschen, 3) * np.exp(-t / 0.010) * 0.12


def bass(midi, dauer):
    t = zeitachse(dauer)
    f = hz(midi - 12)
    s = np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t)
    return s * huelle(len(t), 0.005, 0.05) * np.exp(-t / 0.5)


def ping():
    """Benachrichtigungston, wie ihn ein Telefon macht."""
    t = zeitachse(1.2)
    s = (np.sin(2 * np.pi * 1568 * t) + 0.5 * np.sin(2 * np.pi * 2349 * t)
         + 0.25 * np.sin(2 * np.pi * 3136 * t))
    return s * np.exp(-t / 0.28) * huelle(len(t), 0.002, 0.05) * 0.22


def riser(dauer):
    t = zeitachse(dauer)
    anteil = t / dauer
    rauschen = tiefpass(zufall.normal(0, 1, len(t)), 9)
    # aufsteigender Ton über dem Rauschen
    f = 180 * (12 ** anteil)
    ton = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (0.3 * rauschen * anteil ** 2.5 + 0.3 * ton * anteil ** 1.5) * 0.45


def einschlag():
    t = zeitachse(2.4)
    boom = np.sin(2 * np.pi * (38 + 40 * np.exp(-t / 0.08)) * t) \
        * np.exp(-t / 0.9)
    knall = tiefpass(zufall.normal(0, 1, len(t)), 14) * np.exp(-t / 0.06) * 0.9
    return boom * 0.9 + knall


def hall(signal, dauer=2.4, abklingen=0.55):
    """Faltungshall mit exponentiell abklingendem Rauschen, Stereo."""
    t = zeitachse(dauer)
    ausgabe = []
    for seite in range(2):
        ir = zufall.normal(0, 1, len(t)) * np.exp(-t / abklingen)
        ir[0] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        n = 1 << int(np.ceil(np.log2(len(signal) + len(ir))))
        nass = np.fft.irfft(np.fft.rfft(signal, n) * np.fft.rfft(ir, n), n)
        ausgabe.append(nass[:len(signal)])
    return np.stack(ausgabe)


# --- Arrangement -------------------------------------------------------------
def mischen():
    flaechen = np.zeros(N)
    arp = np.zeros(N)
    schlagwerk = np.zeros(N)
    tief = np.zeros(N)
    effekte = np.zeros(N)

    for takt, noten in enumerate(AKKORDE):
        start = takt * 2.0
        dauer = 2.9 if takt < len(AKKORDE) - 1 else DAUER - start
        hell = 0.25 if start < 8 else (0.6 if start < 12 else 0.9)
        laut = 0.55 if start < 8 else 0.8
        addieren(flaechen, flaeche(noten, dauer, hell) * laut, start)

        # Arpeggio ab 4 s: Achtel, Akkordtöne eine Oktave höher
        if 4.0 <= start < 16.0:
            folge = [n + 12 for n in noten] + [noten[1] + 24]
            schritte = 4 if start < 8 else 8      # erst Viertel, dann Achtel
            for i in range(schritte):
                laut_arp = 0.10 if start < 8 else 0.16
                addieren(arp, pluck(folge[i % len(folge)]) * laut_arp,
                         start + i * 2.0 / schritte)

        # Bass ab dem ersten Einschlag, auf jeder Achtel
        if 8.0 <= start < 16.0:
            for i in range(8):
                addieren(tief, bass(noten[0], 0.24) * 0.35,
                         start + i * SCHLAG / 2)

    # Herzschlag bis zum Einschlag, danach Vierviertel-Kick und Hi-Hats
    for takt in range(4):
        addieren(schlagwerk, herzschlag() * 0.8, takt * 2.0)
    t = 8.0
    while t < 16.0 - 1e-6:
        addieren(schlagwerk, kick(1.0), t)
        addieren(schlagwerk, hihat(), t + SCHLAG / 2)
        t += SCHLAG
    addieren(schlagwerk, kick(1.1), 16.0)

    # Bass duckt unter dem Kick (Sidechain light)
    ducken = np.ones(N)
    for k in np.arange(8.0, 16.0, SCHLAG):
        a = int(k * SR)
        laenge = int(0.18 * SR)
        ducken[a:a + laenge] *= np.linspace(0.25, 1, laenge)
    tief *= ducken
    flaechen *= 0.75 + 0.25 * ducken

    addieren(effekte, ping(), 0.42)
    addieren(effekte, riser(1.4), 6.6)
    addieren(effekte, riser(1.2), 10.8)
    for e in EINSCHLAEGE:
        addieren(effekte, einschlag() * 0.8, e)

    trocken = flaechen + arp + effekte * 0.7
    nass = hall(flaechen * 0.6 + arp + tiefpass(effekte, 8) * 0.4)
    mitte = schlagwerk * 0.9 + tief
    links = trocken + mitte + nass[0] * 0.45
    rechts = trocken + mitte + nass[1] * 0.45
    # Arpeggio leicht in die Breite
    links += np.roll(arp, int(0.011 * SR)) * 0.25
    stereo = np.stack([links, rechts])

    # Ein- und Ausblenden, sanft begrenzen, auf −1 dBFS normalisieren
    stereo *= huelle(N, 0.02, 1.2)
    stereo = np.tanh(stereo * 1.4)
    stereo *= 0.89 / np.max(np.abs(stereo))
    return stereo


def schreiben(stereo, ziel):
    daten = (stereo.T * 32767).astype(np.int16)
    with wave.open(str(ziel), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(daten.tobytes())
    return ziel


def bauen(ziel):
    return schreiben(mischen(), ziel)


if __name__ == "__main__":
    aus = Path(__file__).resolve().parents[1] / "out"
    aus.mkdir(exist_ok=True)
    print("  →", bauen(aus / "trailer-musik.wav"))
