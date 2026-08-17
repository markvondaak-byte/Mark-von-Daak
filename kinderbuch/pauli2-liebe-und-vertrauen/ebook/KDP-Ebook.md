# E-Book bei KDP — „Pauli und der kleine Igel"

Die Datei **`Pauli-und-der-kleine-Igel.epub`** ist ein fertiges, **reflowable
EPUB 3** für Amazon Kindle (Text fließt, passt sich jeder Schriftgröße an).

## Inhalt
- Cover (Hochformat 1600 × 2560 px)
- Titelei, Widmung, Figuren-Vorstellung (inkl. Ida)
- 14 Kapitel mit je einer Illustration und zentriertem Text
- Zitate, Herzens-Gedicht, Herz-Einmaleins, Weiterreden, Quiz, „Wer war wer?"
- Navigierbares Inhaltsverzeichnis

## Metadaten
- **Titel:** Pauli und der kleine Igel
- **Untertitel:** Eine Geschichte über Liebe und Vertrauen – Ein Bilderbuch zum Vorlesen ab 6 Jahren
- **Autor:** Mark von Daak · **Sprache:** Deutsch · **Lesealter:** 6–8
- Beschreibung / Keywords / Kategorien: siehe `../KDP-Stichpunkte.md`
- **Reihe (optional):** „Pauli" (Band 2)

## Veröffentlichen
1. KDP → **„+ Kindle eBook erstellen"** → Details eintragen (KI-Angabe: Ja).
2. Inhalt: **`Pauli-und-der-kleine-Igel.epub`** hochladen (Cover ist enthalten).
3. Mit dem **Kindle Previewer** prüfen, Preis (z. B. **3,99 €**) festlegen, veröffentlichen.
   - 70 % Tantiemen im Preisband 2,60 – 9,99 € · optional **KDP Select** (Kindle Unlimited).

## Neu erzeugen
```
cd kinderbuch/pauli2-liebe-und-vertrauen/ebook && python3 build_epub.py
```
Übernimmt automatisch Änderungen aus `../build_innenteil.py`.
