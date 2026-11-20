#!/usr/bin/env python3
"""Erzeugt die HTML-Vorlagen für die Instagram-Karussells.

    python3 marke/instagram/_vorlage/karussells.py

Stil und Bausteine stammen aus karussell-kniebeugen.html (CSS und Icons
werden von dort übernommen), damit alle Karussells gleich aussehen.
Gerendert wird anschließend mit Playwright (siehe ANLEITUNG.md).
"""
import html
import re
from pathlib import Path

HIER = Path(__file__).resolve().parent
BASIS = (HIER / "karussell-kniebeugen.html").read_text(encoding="utf-8")
CSS = re.search(r"<style>(.*?)</style>", BASIS, re.S).group(1)
DEFS = re.search(r"<defs>(.*?)</defs>", BASIS, re.S).group(1)

EXTRA_CSS = """
  .box.info { background: rgba(56,182,255,.08); border-color: rgba(56,182,255,.45); }
  .box.info .t { color: var(--blue); }
  .uebung h2 { font-size: 104px; margin-top: 40px; }
  .uebung .box ul { font-size: 40px; line-height: 1.45; }
  .uebung .box p { font-size: 38px; }
  .uebung .box { padding: 40px 42px; }
  .chip { display: inline-flex; align-items: center; gap: 12px; margin-top: 30px; padding: 14px 24px; border-radius: 999px; background: rgba(56,182,255,.14); color: var(--blue); font-weight: 600; font-size: 30px; }
  .chip svg { width: 34px; height: 34px; }
  .tabelle { margin-top: 44px; display: grid; gap: 16px; }
  .zeile { display: flex; align-items: center; justify-content: space-between; gap: 20px; background: var(--card); border: 2px solid var(--line); border-radius: 24px; padding: 24px 30px; font-size: 34px; }
  .zeile small { display: block; color: var(--soft); font-size: 26px; margin-top: 4px; }
  .zeile b { font-family: "Inter Display", sans-serif; font-weight: 800; color: var(--blue); font-size: 40px; white-space: nowrap; }
  .zeile.summe { background: var(--blue); border-color: var(--blue); color: var(--dark); font-weight: 600; }
  .zeile.summe b { color: var(--dark); }
  .hinweis { margin-top: 26px; font-size: 26px; color: var(--soft); line-height: 1.4; }
"""

EXTRA_DEFS = """
    <symbol id="uhr" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></symbol>
    <symbol id="info" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="10" stroke-width="2"/><path d="M12 11v6M12 7.5h.01"/></symbol>
"""

FUSS_MARKE = ('<div class="marke"><img src="pin.png" alt=""><div><b>MARK VON DAAK</b>'
              '<span>PERSONAL TRAINING</span></div></div>')


def e(text):
    return html.escape(text, quote=False)


def fuss(nr, gesamt):
    punkte = "".join('<i class="an"></i>' if i == nr else "<i></i>" for i in range(1, gesamt + 1))
    return f'<div class="fuss">{FUSS_MARKE}<div class="punkte">{punkte}</div></div>'


def liste(punkte):
    return "<ul>" + "".join(f"<li>{e(p)}</li>" for p in punkte) + "</ul>"


def folie(nr, gesamt, f):
    art = f["art"]
    if art == "cover":
        inhalt = (f'<div class="gross-zahl">{e(f.get("zahl", ""))}</div>'
                  f'<p class="eyebrow">{e(f["eyebrow"])}</p>'
                  f'<h1>{f["titel"]}</h1><p>{e(f["text"])}</p>'
                  '<span class="wisch">Wischen <svg><use href="#pfeil"/></svg></span>')
        klasse = "cover"
    elif art == "fehler":
        inhalt = (f'<div class="kopf"><span class="nr">{f["nr"]}</span><p class="eyebrow">{e(f["eyebrow"])}</p></div>'
                  f'<h2>{e(f["titel"])}</h2>'
                  f'<div class="box falsch"><p class="t"><svg><use href="#x"/></svg>So nicht</p><p>{e(f["falsch"])}</p></div>'
                  f'<div class="box richtig"><p class="t"><svg><use href="#ok"/></svg>So geht\'s</p>{liste(f["richtig"])}</div>')
        klasse = "fehler"
    elif art == "tipp":
        chip = f'<span class="chip"><svg><use href="#uhr"/></svg>{e(f["chip"])}</span>' if f.get("chip") else ""
        inhalt = (f'<div class="kopf"><span class="nr">{f["nr"]}</span><p class="eyebrow">{e(f["eyebrow"])}</p></div>'
                  f'<h2>{e(f["titel"])}</h2>{chip}'
                  f'<div class="box richtig"><p class="t"><svg><use href="#ok"/></svg>{e(f.get("boxtitel", "So geht\'s"))}</p>{liste(f["punkte"])}</div>')
        if f.get("info"):
            inhalt += f'<div class="box info"><p class="t"><svg><use href="#info"/></svg>{e(f.get("infotitel", "Gut zu wissen"))}</p><p>{e(f["info"])}</p></div>'
        klasse = "uebung"
    elif art == "tabelle":
        zeilen = "".join(f'<div class="zeile"><span>{e(z[0])}<small>{e(z[1])}</small></span><b>{e(z[2])}</b></div>' for z in f["zeilen"])
        zeilen += f'<div class="zeile summe"><span>{e(f["summe"][0])}</span><b>{e(f["summe"][1])}</b></div>'
        inhalt = (f'<p class="eyebrow">{e(f["eyebrow"])}</p><h2 style="font-size:96px;margin-top:36px">{e(f["titel"])}</h2>'
                  f'<div class="tabelle">{zeilen}</div><p class="hinweis">{e(f["hinweis"])}</p>')
        klasse = "check"
    elif art == "check":
        punkte = "".join(f"<li>{e(p)}</li>" for p in f["punkte"])
        inhalt = f'<p class="eyebrow">{e(f["eyebrow"])}</p><h2>{e(f["titel"])}</h2><ol>{punkte}</ol>'
        if f.get("hinweis"):
            inhalt += f'<p class="hinweis">{e(f["hinweis"])}</p>'
        klasse = "check"
    elif art == "cta":
        inhalt = (f'<p class="eyebrow">{e(f["eyebrow"])}</p><h2>{f["titel"]}</h2><p>{e(f["text"])}</p>'
                  '<div class="buttons">'
                  f'<div class="b haupt"><svg><use href="#cal"/></svg>{e(f["knopf"])}</div>'
                  '<div class="b"><svg><use href="#merken"/></svg>Speichern für später</div></div>')
        klasse = "cta"
    else:
        raise ValueError(art)
    return f'<div class="s {klasse}" id="k{nr}">{inhalt}{fuss(nr, gesamt)}</div>'


def seite(folien):
    teile = [folie(i + 1, len(folien), f) for i, f in enumerate(folien)]
    return ("<!DOCTYPE html><html lang=\"de\"><head><meta charset=\"UTF-8\"><style>"
            + CSS + EXTRA_CSS + "</style></head><body>"
            + '<svg width="0" height="0" style="position:absolute"><defs>' + DEFS + EXTRA_DEFS + "</defs></svg>"
            + "\n".join(teile) + "</body></html>")


KARUSSELLS = {
    "liegestuetz": [
        {"art": "cover", "zahl": "3", "eyebrow": "Technik-Check",
         "titel": '3 Fehler bei <span>Liegestütz</span>', "text": "…und wie du sie ab heute korrigierst."},
        {"art": "fehler", "nr": 1, "eyebrow": "Fehler Nummer eins", "titel": "Die Hüfte hängt durch.",
         "falsch": "Der Körper sackt in der Mitte ab. Das belastet den unteren Rücken und die Brust arbeitet kaum.",
         "richtig": ["Körper bildet eine Linie vom Kopf bis zu den Fersen", "Bauch und Po fest anspannen",
                     "Zu schwer? Erst erhöht an Bank oder Wand üben"]},
        {"art": "fehler", "nr": 2, "eyebrow": "Fehler Nummer zwei", "titel": "Die Ellbogen stehen weit ab.",
         "falsch": "Die Arme zeigen wie ein „T“ zur Seite. Das bringt unnötig viel Druck auf die Schultern.",
         "richtig": ["Ellbogen etwa 45 Grad zum Körper", "Hände etwa schulterbreit, unter den Schultern",
                     "Finger zeigen nach vorn"]},
        {"art": "fehler", "nr": 3, "eyebrow": "Fehler Nummer drei", "titel": "Nur die halbe Bewegung.",
         "falsch": "Ein paar Zentimeter runter und wieder hoch. So trainierst du nur einen Teil der Muskulatur.",
         "richtig": ["Brust bis knapp über den Boden", "Oben die Arme ganz strecken",
                     "Lieber weniger Wiederholungen, dafür vollständig"]},
        {"art": "check", "eyebrow": "Zum Speichern", "titel": "Dein Liegestütz in 5 Punkten",
         "punkte": ["Hände unter den Schultern", "Körper eine gerade Linie", "Ellbogen etwa 45 Grad",
                    "Brust bis knapp über den Boden", "Beim Hochdrücken ausatmen"]},
        {"art": "cta", "eyebrow": "Wolfsburg und Umgebung", "titel": 'Mehr Kraft mit <span>Plan?</span>',
         "text": "Im Kennenlern-Training prüfe ich deine Technik bei dir vor Ort und zeige dir, wie du Schritt für Schritt stärker wirst.",
         "knopf": "Kennenlern-Training · Link in Bio"},
    ],
    "eiweiss": [
        {"art": "cover", "zahl": "g", "eyebrow": "Ernährung",
         "titel": 'Eiweiß im <span>Alltag</span>', "text": "So schaffst du dein Eiweiß – ohne Shakes und Rechnerei."},
        {"art": "tipp", "nr": 1, "eyebrow": "Warum Eiweiß?", "titel": "Satt, stark, leichter abnehmen.",
         "boxtitel": "Eiweiß hilft dir", "punkte": ["Macht lange satt", "Unterstützt den Muskelaufbau beim Training",
                                                      "Schützt die Muskeln, wenn du abnimmst"],
         "infotitel": "Richtwert", "info": "Wer Krafttraining macht, liegt oft gut bei etwa 1,6 bis 2 g Eiweiß pro kg Körpergewicht am Tag."},
        {"art": "tipp", "nr": 2, "eyebrow": "Tipp Nummer eins", "titel": "Zu jeder Mahlzeit eine Eiweißquelle.",
         "punkte": ["Faustregel: eine Handfläche Eiweiß pro Mahlzeit", "Zuerst die Eiweißquelle planen, dann den Rest",
                    "Drei Mahlzeiten plus ein Snack reichen oft schon"]},
        {"art": "tipp", "nr": 3, "eyebrow": "Tipp Nummer zwei", "titel": "Das Frühstück aufwerten.",
         "punkte": ["Skyr oder Magerquark mit Beeren und Nüssen", "Rührei oder Omelett mit Gemüse",
                    "Haferflocken mit Quark statt nur mit Milch"]},
        {"art": "tipp", "nr": 4, "eyebrow": "Tipp Nummer drei", "titel": "Snacks clever wählen.",
         "punkte": ["Hüttenkäse oder Skyr", "Edamame oder geröstete Kichererbsen",
                    "Thunfisch, Eier oder Putenaufschnitt"]},
        {"art": "tabelle", "eyebrow": "Beispieltag", "titel": "So kommst du auf über 100 g",
         "zeilen": [["Frühstück", "250 g Skyr mit Beeren", "ca. 27 g"],
                    ["Mittag", "150 g Hähnchenbrust", "ca. 35 g"],
                    ["Snack", "200 g Hüttenkäse", "ca. 24 g"],
                    ["Abendessen", "200 g Tofu mit Gemüse", "ca. 30 g"]],
         "summe": ["Zusammen", "ca. 116 g"],
         "hinweis": "Werte gerundet. Bei Nierenerkrankungen die Eiweißmenge bitte ärztlich abklären."},
        {"art": "cta", "eyebrow": "Ernährungs-Coaching", "titel": 'Ernährung ohne <span>Diätfrust.</span>',
         "text": "Persönliche Kalorien- und Eiweißziele, Rezepte und Einkaufsliste in meiner App SMART Coaching – auch ohne Training buchbar.",
         "knopf": "Jetzt anfragen · Link in Bio"},
    ],
    "rueckentraining-buero": [
        {"art": "cover", "zahl": "5", "eyebrow": "Fit im Büro",
         "titel": 'Rücken&shy;training im <span>Büro</span>', "text": "5 Übungen für zwischendurch – direkt am Schreibtisch."},
        {"art": "tipp", "nr": 1, "eyebrow": "Übung eins", "titel": "Katze und Kuh im Sitzen.", "chip": "10 Wiederholungen",
         "punkte": ["Aufrecht sitzen, Hände auf die Knie", "Ausatmen: Rücken rund, Kinn zur Brust",
                    "Einatmen: Brust nach vorn, leichtes Hohlkreuz"]},
        {"art": "tipp", "nr": 2, "eyebrow": "Übung zwei", "titel": "Schulterblätter zusammen.", "chip": "10 × 3 Sekunden halten",
         "punkte": ["Arme anwinkeln wie ein „U“", "Schulterblätter nach hinten unten ziehen",
                    "Kurz halten, dann locker lassen"]},
        {"art": "tipp", "nr": 3, "eyebrow": "Übung drei", "titel": "Drehung im Sitzen.", "chip": "Je Seite 20 Sekunden",
         "punkte": ["Aufrecht sitzen, Füße fest am Boden", "Oberkörper zur Seite drehen, Hand an die Lehne",
                    "Ruhig weiteratmen, dann Seite wechseln"]},
        {"art": "tipp", "nr": 4, "eyebrow": "Übung vier", "titel": "Hüfte öffnen im Stehen.", "chip": "Je Seite 30 Sekunden",
         "punkte": ["Großer Schritt nach vorn, hinteres Knie leicht gebeugt", "Po anspannen, Becken nach vorn schieben",
                    "Dehnung vorne an der Hüfte spüren"]},
        {"art": "tipp", "nr": 5, "eyebrow": "Übung fünf", "titel": "Kinn zurück.", "chip": "10 × 5 Sekunden halten",
         "punkte": ["Aufrecht sitzen, Blick geradeaus", "Kinn waagerecht nach hinten schieben – Doppelkinn",
                    "Nacken wird lang, Schultern bleiben locker"]},
        {"art": "check", "eyebrow": "Bonus-Tipp", "titel": "Bewegung schlägt die perfekte Haltung",
         "punkte": ["Alle 30 bis 60 Minuten aufstehen", "Telefonate im Stehen oder Gehen",
                    "Bildschirm auf Augenhöhe", "Wasserflasche weiter weg stellen", "Treppe statt Aufzug"],
         "hinweis": "Bei akuten oder anhaltenden Schmerzen bitte ärztlich abklären."},
        {"art": "cta", "eyebrow": "Firmenfitness", "titel": 'Fit im Büro – mit dem ganzen <span>Team?</span>',
         "text": "Workshops „Gesunder Rücken im Büro“ und Einzel-Coachings direkt bei euch in der Firma in Wolfsburg und Umgebung.",
         "knopf": "Jetzt anfragen · Link in Bio"},
    ],
}

if __name__ == "__main__":
    for name, folien in KARUSSELLS.items():
        ziel = HIER / f"karussell-{name}.html"
        ziel.write_text(seite(folien), encoding="utf-8")
        print(ziel.name, len(folien), "Folien")
