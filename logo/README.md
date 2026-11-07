# Logo „V8 fitness HRX-BOX“ als Vektordatei

| Datei | Wofür |
|---|---|
| `v8-fitness-hrx-box.svg` / `.pdf` | Originalfarben (schwarzes V, rote 8) für helle Untergründe, Druck, Shirts |
| `v8-fitness-hrx-box-wand-rot.svg` / `.pdf` | Farben für die rote Wand: V schwarz, 8 weiß, HRX-BOX-Balken weiß mit roter Schrift, Slogan weiß |
| `*-vorschau.png` | Nur zur Ansicht |

Alle Schriften sind in Pfade umgewandelt, die Dateien brauchen also keine installierten Fonts.
Rot: `#E2001A` (nahe RAL 3020 Verkehrsrot), Schwarz: `#000000`, Weiß: `#FFFFFF`.

Nachgebaut nach dem bestehenden V8-Fitness-Logo. V und 8 sind nachgezeichnet, nicht aus der Originaldatei.
Schriften: Oswald Bold („fitness“, „HRX-BOX“) und Barlow Bold (Slogan), beide SIL Open Font License.

Neu erzeugen: Oswald- und Barlow-Fonts (`npm pack @fontsource/oswald @fontsource/barlow`, entpacken) und

    python3 logo/build_logo.py <ordner-mit-den-entpackten-fonts> logo
