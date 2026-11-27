# Rechnungen – eigener Ersatz für invoicehome.com

Erstellt Rechnungen, Angebote, Quittungen und Stornos als PDF, direkt aus
diesem Repository. Es braucht kein Konto, es gibt kein Wasserzeichen und die
Daten liegen nicht auf US-Servern. Alles läuft über
`rechnungen/rechnung.py`.

## Einmalig einrichten

```bash
pip install -r buch/requirements.txt -r rechnungen/requirements.txt
mkdir -p rechnungen/privat
cp rechnungen/bank.beispiel.yaml rechnungen/privat/bank.yaml   # IBAN eintragen
```

Prüfe `rechnungen/absender.yaml`: Telefon, Webseite, Steuernummer und
Kleinunternehmer ja/nein.

## Täglicher Ablauf

| Was | Befehl |
|---|---|
| Neue Rechnung anlegen | `python3 rechnungen/rechnung.py neu rechnung --kunde "Lisa Muster"` |
| Neues Angebot | `python3 rechnungen/rechnung.py neu angebot --kunde "Firma X"` |
| PDF bauen (Nummer wird vergeben) | `python3 rechnungen/rechnung.py bauen rechnungen/belege/<datei>.yaml` |
| Angebot → Rechnung | `python3 rechnungen/rechnung.py umwandeln <angebot.yaml>` |
| Zahlung eingegangen | `python3 rechnungen/rechnung.py bezahlt <rechnung.yaml> --art Überweisung --quittung` |
| Rechnung stornieren | `python3 rechnungen/rechnung.py storno <rechnung.yaml>` |
| Übersicht offen/bezahlt + CSV | `python3 rechnungen/rechnung.py liste --jahr 2026` |
| Paket für die Steuer (ZIP) | `python3 rechnungen/rechnung.py archiv --jahr 2026` |

Arten: `rechnung`, `angebot`, `quittung`, `storno`, `korrektur`, `proforma`,
`lieferschein` und `auftrag` (Auftragsbestätigung). Muster liegen in
`beispiele/`, die Feldbeschreibung steht in `vorlagen/rechnung.yaml`.

## Was übernommen wurde (Vergleich mit invoicehome.com)

| invoicehome.com | hier |
|---|---|
| Rechnung, Angebot, Quittung, Proforma | ✓ dazu Storno, Korrektur, Lieferschein und Auftragsbestätigung |
| Automatische Rechnungsnummern | ✓ je Art und Jahr (`RE-2026-001`), in `absender.yaml` einstellbar |
| Menge, Einheit, Einzelpreis, Beschreibung | ✓ mit Zusatzzeile je Position |
| Mehrere Steuersätze | ✓ 19 %, 7 % und 0 % gemischt, eigene Summen je Satz |
| Rabatt oder Anzahlung als Minusposition | ✓ dazu `rabatt_prozent` für alles |
| Netto- oder Bruttopreise | ✓ `preise: netto` oder `brutto` |
| Fälligkeitsdatum | ✓ aus dem Zahlungsziel berechnet |
| Logo | ✓ `logo:` in `absender.yaml` |
| Online bezahlen (PayPal/Stripe) | `zahlungslink:` wird gedruckt, dazu ein **GiroCode** (QR für Banking-Apps, kostenlos) |
| Als bezahlt markieren | ✓ `bezahlt`, mit Vermerk „Betrag dankend erhalten“ |
| Angebot in Rechnung umwandeln | ✓ `umwandeln` |
| Alle Rechnungen für den Steuerberater | ✓ `archiv`, ZIP mit PDFs und Ausgangsbuch (CSV) |
| Über 150 Währungen | EUR, USD, GBP und CHF mit Symbol, andere als Kürzel |
| Mehr als 100 Designs | ein sauberes Layout nach DIN 5008, Akzentfarbe einstellbar |
| E-Mail-Versand aus dem Dienst | PDF aus `out/` per Mail schicken (bewusst kein Versand aus dem Repo) |

**Zusätzlich, was invoicehome nicht prüft:** die Pflichtangaben nach § 14
Abs. 4 UStG. Beim Bauen erscheint eine Warnung, wenn USt-IdNr.,
Kundenanschrift, Leistungsdatum, Rechnungsbezug beim Storno oder die
USt-IdNr. des Kunden bei Reverse Charge fehlen. Steuerfälle:
`kleinunternehmer` (§ 19), `reverse_charge` (§ 13b), `ig_lieferung` und
`drittland`, jeweils mit dem passenden Pflichthinweis.

## Datenschutz

`belege/` (Kundendaten), `privat/` (IBAN) und `out/` (PDFs) sind
gitignored, weil dieses Repository öffentlich ist. Die Belege bewahrst du
selbst 8 Jahre lang auf (§ 14b UStG, § 147 AO), zum Beispiel per
`archiv`-ZIP in deiner Cloud.

## E-Rechnung (bitte vor Nutzung prüfen)

Seit 2025 musst du E-Rechnungen von Firmen *empfangen* können. Für
**ausgehende** Rechnungen an Firmen (B2B, Inland) darfst du nach meinem
Stand bei einem Vorjahresumsatz bis 800.000 € noch **bis Ende 2027** ein PDF
schicken, wenn der Kunde zustimmt. Ab 2028 muss es XRechnung oder ZUGFeRD
sein. Für Privatkunden (B2C) bleibt das PDF erlaubt. Die Daten hier
(Positionen, Steuersätze) reichen für eine spätere ZUGFeRD-Ausgabe. Lass die
Fristen von deinem Steuerberater bestätigen.

## FitLine-Rechnungen

Absender ist **Wellness 4 You Wolfsburg** (Inhaber Mark von Daak), Profil
`absender-fitline.yaml`. Andere Absender gehen genauso: `absender-<name>.yaml`
anlegen und im Beleg `absender: <name>` setzen.

Produkte, Endkundenpreise (brutto) und Steuersätze stehen in
`kataloge/fitline.yaml`. Eine Position braucht dann nur noch `artikel:` und
`menge:`.

```bash
python3 rechnungen/rechnung.py artikel fitline                           # Produktliste
python3 rechnungen/rechnung.py neu rechnung --vorlage fitline --kunde "Lisa Muster"
python3 rechnungen/rechnung.py bauen rechnungen/belege/<datei>.yaml
```

Der Katalog enthält **alle Produkte des offiziellen FitLine-Shops**
(Artikelnummer, Endkundenpreis, Steuersatz wie von FitLine deklariert) und
wird automatisch erzeugt. Preise aktualisieren:

```bash
python3 rechnungen/kataloge/fitline_aktualisieren.py   # zeigt geänderte Preise an
```

Positionen gehen per Schlüssel (`powercocktail`), Kurzname (`optimal-set`,
`restorate`, `activize` …) oder Artikelnummer (`artikel: "0705067"`).

## Nummern über Sitzungen hinweg

`nummern.json` enthält nur die Zählerstände (keine Kundendaten) und wird
committet. So läuft der Nummernkreis auch in einer neuen Cloud-Sitzung
lückenlos weiter. Belege und PDFs bleiben lokal bzw. werden dir geschickt.

## Private Ablage (empfohlen)

Liegt neben diesem Repository ein Ordner mit der Datei `.rechnungsablage`
(oder ist `RECHNUNG_ABLAGE` gesetzt), speichert das Skript alles mit
Kundendaten dort:

```
rechnungen/            ← privates Repository markvondaak-byte/rechnungen
  .rechnungsablage
  belege/              Beleg-YAMLs
  pdf/                 PDFs, Ausgangsbuch, ZIP-Archive
  privat/bank.yaml     Bankverbindung
  nummern.json         Nummernzähler
```

`python3 rechnungen/rechnung.py sichern` committet und pusht die Ablage.
