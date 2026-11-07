"""Baut das Logo 'V8 fitness HRX-BOX' als reine Vektorgrafik (Schrift in Pfade umgewandelt)."""
import sys, os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
import cairosvg

FD, OUT = sys.argv[1], sys.argv[2]
OSWALD = TTFont(os.path.join(FD, "fontsource-oswald-5.3.0/package/files/oswald-latin-700-normal.woff"))
BARLOW = TTFont(os.path.join(FD, "fontsource-barlow-5.3.0/package/files/barlow-latin-700-normal.woff"))

def glyph(font, ch):
    gs = font.getGlyphSet(); name = font.getBestCmap()[ord(ch)]
    bp = BoundsPen(gs); gs[name].draw(bp)
    return gs, name, bp.bounds, font["hmtx"][name][0]

def draw(font, ch, x, base, s):
    gs, name, b, adv = glyph(font, ch)
    sp = SVGPathPen(gs)
    gs[name].draw(TransformPen(sp, (s, 0, 0, -s, x, base)))
    return sp.getCommands()

def justify(font, text, x0, x1, base, height, ref):
    """Buchstaben so verteilen, dass die Tinte genau von x0 bis x1 reicht, gleiche Abstände."""
    rb = glyph(font, ref)[2]; s = height / (rb[3] - max(rb[1], 0))
    gl = [glyph(font, c) for c in text]
    inks = [(g[2][2] - g[2][0]) * s for g in gl]
    gap = (x1 - x0 - sum(inks)) / (len(text) - 1)
    d, x = [], x0
    for c, g, w in zip(text, gl, inks):
        d.append(draw(font, c, x - g[2][0] * s, base, s)); x += w + gap
    return " ".join(d)

def tracked(font, text, cx, base, height, track):
    rb = glyph(font, "H")[2]; s = height / rb[3]
    gl = [glyph(font, c) for c in text]
    w = sum(g[3] * s for g in gl) + track * (len(text) - 1)
    x, d = cx - w / 2, []
    for c, g in zip(text, gl):
        if c != " ": d.append(draw(font, c, x, base, s))
        x += g[3] * s + track
    return " ".join(d)

V = "M110 160 H252 L360 392 L468 160 H610 L428 466 Q408 500 360 500 Q312 500 292 466 Z"
EIGHT = ("M58 0 H282 Q340 0 340 58 V142 L314 165 L340 188 V272 Q340 330 282 330 "
         "H58 Q0 330 0 272 V188 L26 165 L0 142 V58 Q0 0 58 0 Z "
         "M128 70 H246 Q274 70 274 99 Q274 128 246 128 H128 Q100 128 100 99 Q100 70 128 70 Z "
         "M94 202 H212 Q240 202 240 231 Q240 260 212 260 H94 Q66 260 66 231 Q66 202 94 202 Z")

FIT  = justify(OSWALD, "fitness", 218, 912, 652, 104, "f")
HRX  = justify(OSWALD, "HRX-BOX", 118, 897, 803, 96, "H")
TAG  = tracked(BARLOW, "RUN · LIFT · RACE", 507, 900, 32, 14)

RED, BLACK, WHITE = "#E2001A", "#000000", "#FFFFFF"

def svg(c):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="40 130 940 800" width="940" height="800">
  <title>V8 fitness HRX-BOX</title>
  {f'<rect x="40" y="130" width="940" height="800" fill="{c["bg"]}"/>' if c.get("bg") else ""}
  <path id="v" d="{V}" fill="{c["v"]}"/>
  <path id="acht" d="{EIGHT}" fill="{c["eight"]}" fill-rule="evenodd" transform="translate(646 160) skewX(-23)"/>
  <rect id="balken-fitness" x="60" y="538" width="895" height="130" fill="{c["bar1"]}"/>
  <path id="text-fitness" d="{FIT}" fill="{c["t1"]}"/>
  <rect id="balken-hrx-box" x="60" y="688" width="895" height="140" fill="{c["bar2"]}" stroke="{BLACK}" stroke-width="3"/>
  <path id="text-hrx-box" d="{HRX}" fill="{c["t2"]}"/>
  <path id="slogan" d="{TAG}" fill="{c["tag"]}"/>
</svg>
'''

variants = {
  "v8-fitness-hrx-box": dict(v=BLACK, eight=RED, bar1=BLACK, t1=WHITE, bar2=RED, t2=WHITE, tag=BLACK),
  "v8-fitness-hrx-box-wand-rot": dict(v=BLACK, eight=WHITE, bar1=BLACK, t1=WHITE, bar2=WHITE, t2=RED, tag=WHITE),
}
for name, c in variants.items():
    p = os.path.join(OUT, name)
    open(p + ".svg", "w").write(svg(c))
    cairosvg.svg2pdf(url=p + ".svg", write_to=p + ".pdf")
    prev = dict(c, bg="#FFFFFF" if "wand" not in name else RED)
    cairosvg.svg2png(bytestring=svg(prev).encode(), write_to=p + "-vorschau.png", output_width=1880)
print("ok")
