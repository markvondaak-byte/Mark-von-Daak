# Vorgaben für neue Bücher (Amazon KDP)

Mark von Daak veröffentlicht Ratgeber im Selbstverlag über Amazon KDP. Wenn
er ein neues Buch „mit den gleichen Vorgaben wie in den letzten Büchern“
möchte, gilt diese Datei. Vorlage ist der zuletzt fertiggestellte Titel
**„Der Narzisst in meinem Bett“** im Ordner `narzisst/` — für ein neues Buch
diesen Ordner als Muster nehmen (eigener Ordner, eigene YAML, eigene
Build-Skripte), nicht die Reihe in `buch/`.

Sprache mit dem Nutzer: Deutsch, du-Form. Fertige Dateien (PDF, EPUB, Cover,
Video) mit SendUserFile schicken — `*/out/` ist gitignored.

## Was zu einem Buch gehört

1. **Innenteil** `<ordner>/out/<slug>-druck.pdf` — 6 × 9 Zoll (152,4 × 228,6 mm),
   Ränder innen 20, außen 16, oben/unten 18 mm, Schwarzweiß, weißes Papier,
   **mindestens 76 Seiten** und gerade Seitenzahl (KDP-Hardcover ab 75 Seiten;
   Taschenbuch und Hardcover teilen sich einen Innenteil). Fehlende Seiten
   mit Inhalt füllen (Fallgeschichten, Kapitel für Angehörige, Anlaufstellen,
   häufige Fragen), nie mit Leerraum.
2. **Word-Manuskript** `<slug>.docx` — entsteht beim Bauen mit.
3. **Umschläge** `cover-druck.pdf` (Taschenbuch, 3,175 mm Anschnitt) und
   `cover-hardcover-druck.pdf` (18 mm Umschlagrand, Rücken + 9 mm). Als
   Rasterbild bei 300 dpi in ein PDF exakter Größe, ohne Transparenz.
   Barcodefeld hinten unten rechts frei lassen, ohne eigene Weißfläche.
   Rückentext erst ab 79 Seiten (Taschenbuch), beim Hardcover immer.
4. **Kindle** `<slug>-kindle.epub` (fließender Text, eigene UUID) und
   `kindle-cover.jpg` (1600 × 2560 px).
5. **Werbevideo** `werbevideo-9x16.mp4` — 1080 × 1920, ca. 25 s, ohne Ton,
   Bild für Bild mit Pillow + ffmpeg (Muster: `narzisst/build/build_video.py`):
   Hook, Wiedererkennen, Wendung, Inhalte, Buch-Mockup mit „Jetzt erhältlich ·
   Taschenbuch · Hardcover · E-Book · bei Amazon“. Jede Aussage muss im Buch
   stehen.
6. **Klappentext** `cover/klappentext.md` (Schlagzeile, 1–2 Absätze,
   Stichpunkte mit fettem Kopf).
7. **Amazon-Beschreibung** `cover/amazon-beschreibung.md`: Lesefassung,
   KDP-HTML (nur h4, h5, p, b, i, ul, li; unter 4.000 Zeichen), dazu eine
   **Zusammenfassung** (~750 Zeichen) und ein **Einzeiler**. Wenn der Nutzer
   nach der Beschreibung fragt, den Text zusätzlich direkt im Chat zum
   Einfügen geben.
8. **KDP-Metadaten** — eigener Abschnitt in `kdp-metadaten.md`: Titel,
   Untertitel, Seiten, Maße beider Bindearten, Dateien, Kategorien (drei,
   mit Begründung; Knoten-IDs nur, wenn sicher bekannt), **7 Keywords**,
   Ersatz-Keywords, KI-Angabe, Autorentext für diesen Titel.

Bauen (Beispiel narzisst): `build_narzisst.py` → `build_cover.py` →
`build_epub.py` → `build_video.py`. Der Umschlag hängt an der Seitenzahl —
nach jeder Textänderung Innenteil **und** Umschläge neu bauen.
Voraussetzungen: `pip install -r buch/requirements.txt pyspellchecker`,
LibreOffice (`libreoffice-writer`).

## Inhalt und Aufbau

- Titelseite · Impressum · Bitte zuerst lesen (Grenzen des Buches, bei
  belastenden Themen Notruf und Hilfetelefone) · Inhalt · Vorwort (für wen,
  Aufbau, wie lesen) · Teile mit nummerierten Kapiteln (je ~800–1.100 Wörter)
  · Schlusswort („Das Buch in sieben Sätzen“) · Quellen nach Kapiteln ·
  Über den Autor (mit Bitte um ehrliche Rezension).
- **Keine Übungen und kein Arbeitsteil**, solange nicht ausdrücklich
  gewünscht. Stattdessen endet jedes Kapitel mit einem Kasten
  `> Kurz gefasst:`.
- Ton: warm, klar, ohne Fachchinesisch, du-Form; Studien vereinfacht und
  belegt; keine Diagnosen, keine Heil- oder Ergebnisversprechen.
- Lange H1-Überschriften mit geschützten Leerzeichen sauber umbrechen
  (kein Einzelwort in der zweiten Zeile).
- Vor dem Abschluss `buch/build/rechtschreibung.py` mit den eigenen
  Ordnern laufen lassen (deutsche Anführungszeichen „…“, Gedankenstrich —).

## Impressum

Ausführlich, in **8 pt auf einer Seite** (Muster:
`narzisst/kapitel/01-impressum.md` + `impressum_verkleinern()`):
Titel/Untertitel · 1. Auflage + © Jahr Mark von Daak · ISBN-Platzhalter
`{{ISBN}}` (aus der YAML gefüllt, leer und im E-Book entfällt die Zeile) ·
Herausgeber und Verlag (Selbstverlag): Mark von Daak, Rabenbergstraße 16,
38444 Wolfsburg, Deutschland, markvondaak@icloud.com, USt-IdNr. DE319920422 ·
Verantwortlich für den Inhalt nach den Pressegesetzen · Umschlaggestaltung
und Satz, Herkunft des Umschlagbildes, Druck über Amazon KDP · Urheberrecht
mit TDM-Vorbehalt nach § 44b UrhG · Haftungsausschluss · Hinweise zu
Rufnummern/Rechtslage, Fallbeispielen, Sprache · Markenhinweis.

**Nicht ins Impressum:** kein Transparenzhinweis zur Vertriebstätigkeit,
kein Hinweis der Deutschen Nationalbibliothek. (Pflichtexemplare an die DNB
sind trotzdem fällig, sobald eine ISBN vergeben ist — in den Metadaten
vermerken.)

## Umschlag

- Titelbild meist ein vom Nutzer geliefertes Higgsfield-Foto unter
  `<ordner>/cover/titelbild.png`: Wasserzeichen unten rechts
  herausschneiden, Ausschnitt so legen, dass das Motiv bleibt, unten in den
  Grundton abdunkeln (ins Bild gerechnet), Rücken und Rückseite in den
  Randtönen des Fotos. Auflösung prüfen und melden, wenn hochgerechnet wird.
- Ohne Foto ein gezeichnetes Motiv (Pillow), passend zum Thema.
- Schrift Inter Display (`/usr/share/fonts/opentype/inter/`), Titel in
  Black, letzte Titelzeile in der Akzentfarbe, Autor gesperrt in Versalien.
- Rückseite: Schlagzeile, Klappentext, Stichpunkte, „Über den Autor“, kurzer
  Hinweis (kein Ersatz für Beratung; bei Gefahr Notruf/Hilfetelefon).

## KDP-Regeln

- Keywords: 7 Felder, je ≤ 50 Zeichen, Wortgruppen; **kein Wort aus Titel
  oder Untertitel, kein Wort doppelt**, keine Marken, keine Versprechen.
  Mit einem kurzen Skript prüfen.
- KI-Angabe: Text mit Claude erzeugt → „KI-erzeugter Text: ja“;
  Higgsfield-Bild → „KI-erzeugte Bilder: ja“. Lizenz für kommerzielle
  Nutzung des Bildes ansprechen.
- Kein Serienfeld bei eigenständigen Titeln. Keine fremden Marken, keine
  erfundenen Rezensionen oder Zitate, keine Kilogramm-/Heilversprechen.
- Autorentext ehrlich: Mark ist kein Arzt, Psychologe oder Therapeut.

## Arbeitsweise

- Titelvorschläge des Nutzers übernehmen; nur kurz eine Einschätzung geben,
  wenn er fragt.
- Nach jedem Schritt committen und auf den zugewiesenen Branch pushen;
  Commit-Nachrichten auf Deutsch, beginnend mit dem Buchtitel.
- Nummern von Hilfetelefonen und Quellenangaben als „bitte vor Upload
  prüfen“ kennzeichnen, wenn sie nicht online verifiziert wurden.
