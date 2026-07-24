# Sechs Minuten für mich — Achtsamkeits- & Dankbarkeitstagebuch für Amazon KDP

Ein komplett eigenständiges, druckfertiges Tagebuch (180 Tage, Morgen- & Abendritual),
das du direkt bei **Amazon KDP** als Taschenbuch veröffentlichen kannst.

## Dateien

| Datei | Zweck |
|-------|-------|
| `generate_journal.py` | Generator-Skript (erzeugt beide PDFs neu) |
| `innenseiten_6x9.pdf` | **Buchblock / Interior** — bei KDP als „Manuskript" hochladen |
| `cover_6x9.pdf` | **Umschlag / Cover** — bei KDP als „Buchcover" hochladen |

Neu erzeugen jederzeit mit:

```bash
pip install reportlab
python3 generate_journal.py
```

---

## Technische Eckdaten (bereits KDP-konform)

| Merkmal | Wert |
|---------|------|
| Format (Trim Size) | 15,24 × 22,86 cm (6" × 9") |
| Seitenzahl | **220** (gerade – Pflicht bei KDP) |
| Bundsteg innen | 12,7 mm (0,5") – korrekt für 151–300 Seiten |
| Außenränder | 9,5 mm (0,375") |
| Ränder | gespiegelt (recto/verso) für sauberen Buchdruck |
| Papierannahme | Creme, 55–60 g |
| Buchrücken | **14,0 mm** (0,55") – berechnet aus 220 Seiten × Creme |
| Cover-Gesamtmaß | 32,5 × 23,5 cm (inkl. 3,2 mm Beschnitt/Bleed) |
| Barcode-Feld | freigehalten (weiß) unten rechts auf der Rückseite |

> **Wichtig:** Rückenbreite und Cover-Maße hängen von Seitenzahl **und** Papiersorte ab.
> Ändere Umfang oder Papier, muss das Cover neu generiert werden (Skript macht das automatisch).
> Für **weißes** statt cremefarbenes Papier: im Skript `PAPER = 0.002252 * inch` setzen.

---

## Schritt für Schritt bei KDP veröffentlichen

1. Anmelden auf **kdp.amazon.com** → *Taschenbuch erstellen*.
2. **Buchdetails:** Titel, Untertitel, Autor, Beschreibung (Klappentext siehe unten),
   Kategorien (z. B. *Ratgeber › Selbsthilfe* / *Kalender & Tagebücher*), 7 Keywords.
3. **Inhalt:**
   - Druck: Schwarzweiß
   - Papier: **Creme** (passend zur berechneten Rückenbreite)
   - Format: **6 × 9 Zoll**
   - Manuskript hochladen: `innenseiten_6x9.pdf`
   - Cover hochladen (Option „Eigenes PDF-Cover verwenden"): `cover_6x9.pdf`
4. **Vorschau prüfen** im KDP-Previewer (Ränder, Bundsteg, Barcode-Feld).
5. Preis & Rechte festlegen → **Veröffentlichen**.

Die kostenlose ISBN von KDP genügt; den Barcode setzt Amazon automatisch in das
freigehaltene weiße Feld.

---

## Fertiger Klappentext (zum Kopieren in die KDP-Beschreibung)

> **Nimm dir sechs Minuten. Für dich.**
>
> Drei Minuten am Morgen, drei Minuten am Abend – mehr braucht es nicht, um deinen
> Blick jeden Tag ein Stück weit auf das Gute zu lenken. Dieses liebevoll gestaltete
> Tagebuch begleitet dich 180 Tage lang mit einem einfachen, wohltuenden Ritual aus
> Dankbarkeit, Fokus und Achtsamkeit.
>
> **Dein tägliches Ritual:**
> - ☀ Morgens: Dankbarkeit, Tagesfokus und eine stärkende Affirmation
> - 🌙 Abends: schöne Momente, persönliches Wachstum und ein ruhiger Ausblick
> - 📆 Wöchentliche Rückblicke und Platz für eigene Notizen
>
> Klar strukturiert, warm gestaltet und ohne erhobenen Zeigefinger. Beginne heute –
> und schenke dir jeden Tag einen Moment nur für dich.

---

## ⚠️ Rechtlicher Hinweis (bitte lesen)

- **„Das 6-Minuten-Tagebuch"** ist ein eingetragener Marken-/Produkttitel eines
  anderen Verlags. Das **Konzept** eines Morgen-/Abend-Dankbarkeitstagebuchs ist
  frei nutzbar, der geschützte **Titel und konkrete Formulierungen** sind es nicht.
  Dieses Produkt trägt deshalb einen eigenständigen Titel (*„Sechs Minuten für
  mich"*) und **eigene, selbst verfasste Texte**. Verwende bei KDP **nicht** den
  geschützten Fremdtitel, um Markenbeschwerden zu vermeiden.
- Der Titel ist ein Vorschlag – prüfe vor Veröffentlichung kurz, ob er markenrechtlich
  frei ist (z. B. DPMA-Register), und passe ihn bei Bedarf im Skript an (`TITLE`).
- Trage im **Impressum/Copyright** (Skript-Variable `AUTHOR_PLACEHOLDER`) deinen
  Namen bzw. deine Verlagsangabe ein, bevor du druckst.

---

## Anpassen

Alle Stellschrauben stehen oben im Skript unter **KONFIGURATION**:

- `TITLE`, `TITLE_DISP`, `SUBTITLE` – Titel & Untertitel
- `DAYS` – Anzahl der Tagesseiten (z. B. 90, 180, 365)
- `AUTHOR_PLACEHOLDER`, `YEAR` – Copyright-Angaben
- Farben im Abschnitt **FARBEN** (aktuell warmes Terracotta/Sand)
- Tages-Impulse in der Liste `IMPULSES`
