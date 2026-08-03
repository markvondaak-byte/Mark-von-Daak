# Hosting bei Netlify

## Was veröffentlicht wird

| Pfad | Inhalt |
|---|---|
| `/` | Website (`index.html`, Impressum, Datenschutz) |
| `/app/` | Die Stoffwechsel-Reset-App |
| `/assets/` | Bilddateien |
| `/404.html` | Fehlerseite im Look der Website |

**Nicht** veröffentlicht werden die Buchquellen unter `buch/`, `workbook/` und
`rezepte/` sowie sämtliche Build-Skripte. Dafür sorgt `tools/build_site.py`:
Es kopiert gezielt nur das Auszuliefernde nach `dist/` und bricht mit einem
Fehler ab, falls doch eine Buchquelle darin landet.

## Einrichtung, einmalig

1. Auf [netlify.com](https://app.netlify.com) anmelden (GitHub-Login geht).
2. **Add new site → Import an existing project → GitHub**, dann dieses
   Repository auswählen.
3. Netlify liest `netlify.toml` und schlägt die richtigen Werte vor. Zur
   Kontrolle:

   | Feld | Wert |
   |---|---|
   | Branch to deploy | `main` |
   | Build command | `python3 tools/build_site.py` |
   | Publish directory | `dist` |

4. **Deploy site**. Der erste Build dauert etwa eine Minute.

Danach ist die Seite unter einer Adresse wie
`https://zufallsname-123456.netlify.app` erreichbar.

## Eigene Domain

Unter **Domain management → Add a domain** die Wunschdomain eintragen.

Netlify nennt dann die nötigen DNS-Einträge — entweder Netlifys Nameserver
beim Domain-Anbieter hinterlegen (bequemer) oder einen A- und einen
CNAME-Eintrag setzen.

Das TLS-Zertifikat stellt Netlify automatisch über Let's Encrypt aus, sobald
die DNS-Einträge greifen. Das kann bis zu 24 Stunden dauern, meist geht es
schneller.

**HTTPS ist für die App keine Kür, sondern Voraussetzung.** Ohne gesicherte
Verbindung registriert kein Browser einen Service Worker — und ohne den gibt
es weder Offline-Betrieb noch die Installation auf dem Homescreen.

## Was in `netlify.toml` geregelt ist

- **Sicherheitskopfzeilen** für alle Antworten: `X-Frame-Options`,
  `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy` und HSTS.
- **HTML wird nicht gecacht.** Sonst sehen Besucher nach einer Änderung
  tagelang die alte Seite.
- **Bilder und App-Icons ein Jahr lang**, weil sie feste Namen tragen.
- **Der Service Worker wird nie gecacht.** Das ist der kritischste Punkt
  überhaupt — siehe unten.
- `/app` leitet auf `/app/` um.
- `/buch/*`, `/workbook/*` und `/rezepte/*` geben eine saubere 404 zurück.

## Nach jedem Update

Ein `git push` auf `main` löst automatisch einen neuen Build aus. Zwei Dinge
sind dabei zu beachten:

**1. Nach Änderungen an den Büchern die App-Daten neu erzeugen:**

```bash
python3 app/build/build_app_daten.py
```

Sonst zeigt die App weiterhin den alten Stand — sie liest ihre Inhalte aus
`app/daten/*.json`, und die werden aus den Buchquellen generiert.

**2. Nach Änderungen an der App die Cache-Version hochzählen.**

In `app/sw.js` steht:

```js
const VERSION = 'stoffwechsel-reset-v1';
```

Erhöhe die Zahl bei jedem Update auf `-v2`, `-v3` und so weiter. Ohne das
liefert der Service Worker bei allen bestehenden Nutzern weiter die alten
Dateien aus — sie bekämen dein Update nie zu sehen. Das ist der häufigste
Fehler beim Betrieb einer PWA.

## Vorher lokal prüfen

```bash
python3 tools/build_site.py
cd dist && python3 -m http.server 8877
```

Dann `http://127.0.0.1:8877` öffnen. Die App liegt unter `/app/`.

Ein Server ist nötig: Die App lädt ihre Daten per `fetch`, und das
funktioniert bei einem direkt geöffneten `file://` nicht.

## Wenn etwas nicht stimmt

**Der Build schlägt fehl.** Im Netlify-Log nachsehen. Das Skript nutzt
ausschließlich die Python-Standardbibliothek, es muss also nichts installiert
werden. Häufigste Ursache: eine umbenannte Datei, die noch in `DATEIEN` oder
`VERZEICHNISSE` in `tools/build_site.py` steht.

**Die App zeigt alte Inhalte.** Der Service Worker liefert aus dem Cache.
`VERSION` in `app/sw.js` erhöhen und neu deployen. Zum Testen bei dir selbst:
in den Entwicklerwerkzeugen unter *Application → Storage → Clear site data*.

**Die App lässt sich nicht installieren.** Prüfen, ob die Seite wirklich über
HTTPS läuft und ob `/app/manifest.webmanifest` erreichbar ist. Chrome zeigt
unter *Application → Manifest* an, was fehlt.

**Die Seite ist da, aber die App nicht.** `tools/build_site.py` bricht ab,
wenn Pflichtdateien der App im `dist` fehlen — dann steht die Ursache im
Build-Log.

## Noch offen

Von der Website führt derzeit **kein Link zur App**. Wer sie nutzen soll,
muss die Adresse kennen. Ein Verweis in `index.html` wäre ein kleiner
Eingriff — sag Bescheid, wenn du ihn möchtest, dann baue ich ihn passend in
den bestehenden Aufbau ein.
