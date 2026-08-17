# E-Book bei Amazon KDP — „Pauli und das kleine Licht"

Die Datei **`Pauli-und-das-kleine-Licht.epub`** ist ein fertiges, **reflowable
EPUB 3** – genau das Format, das Amazon KDP für Kindle-E-Books akzeptiert.

> **Reflowable** heißt: Der Text passt sich automatisch an jede Bildschirmgröße
> und Schriftgröße an (anders als das feste Druck-PDF). Zu jedem Kapitel ist die
> Illustration als Bild eingebettet, das Cover steckt bereits im EPUB.

---

## Was drin ist
- Cover (Hochformat, 1600 × 2560 px – ideal für Kindle)
- Titelei, Widmung, Figuren-Vorstellung
- 14 Kapitel mit je einer Illustration und zentriertem Text
- Zitat-Sätze, Mutmach-Gedicht, „Mut-Einmaleins", Weiterreden, Quiz, „Wer war wer?"
- Navigierbares Inhaltsverzeichnis (Kindle-TOC)

Nicht enthalten sind die reinen **Mitmach-Seiten** (Labyrinth, Mal-Seite,
Ausfüllblatt) – die funktionieren nur im gedruckten Buch.

---

## Metadaten (wie beim Taschenbuch)
- **Titel:** Pauli und das kleine Licht
- **Untertitel:** Eine Geschichte über Mut und Freundschaft – Ein Bilderbuch zum Vorlesen ab 6 Jahren
- **Autor:** Mark von Daak *(anpassbar)*
- **Sprache:** Deutsch · **Lesealter:** 6–8
- **Beschreibung / Keywords / Kategorien:** siehe `../Amazon-Produktbeschreibung.md`
  bzw. die Taschenbuch-Anleitung – sie gelten unverändert.

---

## Preis & KDP Select
- Übliche Preisspanne für ein Kinder-E-Book: **2,99 – 4,99 €**.
- **70 % Tantiemen** gibt es bei KDP nur im Preisband **2,60 – 9,99 €**
  (darunter/darüber 35 %).
- Optional **KDP Select** (90 Tage Exklusivität): dann ist das Buch in „Kindle
  Unlimited" lesbar und du wirst nach gelesenen Seiten vergütet.

---

## Schritt für Schritt
1. Auf **kdp.amazon.com** → **„+ Kindle eBook erstellen"**.
2. **Details:** Titel, Untertitel, Autor, Beschreibung, Keywords, Kategorien,
   Lesealter eintragen (KI-Frage wahrheitsgemäß beantworten – Text und Bilder
   sind KI-erstellt).
3. **Inhalt (zwei Upload-Felder):**
   - **eBook-Manuskript (= Innenteil):** **`Pauli-und-das-kleine-Licht.epub`** hochladen.
   - **eBook-Cover:** **`ebook-cover.jpg`** hochladen (JPEG, 1600 × 2560 px –
     genau das KDP-Wunschformat). Das Cover steckt zwar auch im EPUB, aber KDP
     möchte es zusätzlich als separates Bild für Produktseite und Thumbnail.
4. **Vorschau:** Mit dem **Kindle Previewer** (bzw. der Online-Vorschau) einmal
   durch alle Kapitel klettern – prüfen, ob Bilder laden und der Text sauber fließt.
5. **Preis** festlegen (Abschnitt oben), Länder wählen, **veröffentlichen**.

---

## Neu erzeugen / anpassen
Das E-Book wird aus demselben Text wie das Druckbuch gebaut:

```
cd kinderbuch/ebook && python3 build_epub.py
```

Änderst du die Geschichte im Druck-Generator (`../buch-6x9/build_innenteil.py`),
übernimmt das E-Book die Änderung beim nächsten Lauf automatisch.

> **Tipp:** Amazon empfiehlt, EPUBs vor dem Hochladen mit dem kostenlosen
> **Kindle Previewer** zu testen – dort siehst du das Buch exakt wie auf einem
> Kindle.
