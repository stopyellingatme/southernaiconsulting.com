#!/usr/bin/env python3
"""Generate the print-ready brand asset set into brand/.

    python3 tools/make_brand_assets.py

Why this script exists: logo-lockup.svg uses a live <text> element in Georgia.
A print shop without Georgia silently substitutes another face and the logo is
wrong on the finished cards. Everything produced here has the wordmark
converted to real vector outlines via fontTools, so there is no font
dependency at any point in the print chain.

Outputs (brand/):
  logo-mark-{colour,navy,black,white}.svg        mark alone
  logo-horizontal-{colour,navy,black,white}.svg  mark + wordmark, side by side
  logo-stacked-{colour,navy,black,white}.svg     mark above wordmark
  *.png                                          300 dpi, transparent
"""

import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image, ImageDraw, ImageFont

OUT = "brand"
GEORGIA_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"

NAVY = "#10233A"
COPPER = "#B26B3F"
CREAM = "#FBF9F6"
BLACK = "#000000"
WHITE = "#FFFFFF"

# ── mark geometry, identical to logo.svg (64x64 design box) ───────────────
# Point-symmetric about (32,32): rotating any control point 180 degrees about
# the centre lands on another control point. Keep it that way if you edit it.
CURVES = [
    ((48.2, 12), (21.2, 12), (21.2, 26), (32, 32)),
    ((32, 32), (42.8, 38), (42.8, 52), (15.8, 52)),
]
STROKE_W = 8.5

LINE1, LINE2 = "SOUTHERN AI", "CONSULTING"
TEXT_SIZE = 19.0
TRACKING = 0.6          # px of extra letter-spacing at TEXT_SIZE

_font = TTFont(GEORGIA_BOLD)
_glyphs = _font.getGlyphSet()
_cmap = _font.getBestCmap()
_upem = _font["head"].unitsPerEm


def glyph_run(text, size, tracking):
    """Outline `text` as SVG path data plus its advance width in px.

    Returned paths are in font units; the caller wraps them in a transform
    that scales by size/upem and flips Y (fonts are Y-up, SVG is Y-down).
    """
    scale = size / _upem
    track_units = tracking / scale
    x, parts = 0.0, []
    for ch in text:
        gname = _cmap[ord(ch)]
        pen = SVGPathPen(_glyphs)
        _glyphs[gname].draw(pen)
        d = pen.getCommands()
        if d:
            parts.append(f'<path transform="translate({x:.2f} 0)" d="{d}"/>')
        x += _glyphs[gname].width + track_units
    width = (x - track_units) * scale if text else 0.0
    return parts, width


def text_width(text):
    _, w = glyph_run(text, TEXT_SIZE, TRACKING)
    return w


def text_bbox(x, baseline, text):
    """Exact ink bounds of an outlined run, in px, y-down like SVG."""
    scale = TEXT_SIZE / _upem
    track_units = TRACKING / scale
    pen_x = 0.0
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    for ch in text:
        gname = _cmap[ord(ch)]
        bp = BoundsPen(_glyphs)
        _glyphs[gname].draw(bp)
        if bp.bounds:
            gx0, gy0, gx1, gy1 = bp.bounds
            x0 = min(x0, x + (pen_x + gx0) * scale)
            x1 = max(x1, x + (pen_x + gx1) * scale)
            # font y-up -> SVG y-down about the baseline
            y0 = min(y0, baseline - gy1 * scale)
            y1 = max(y1, baseline - gy0 * scale)
        pen_x += _glyphs[gname].width + track_units
    return x0, y0, x1, y1


def mark_bbox(dx=0.0, dy=0.0):
    """Ink bounds of the mark: the stroke envelope, sampled along both curves.

    Round caps mean the envelope is the path offset by half the stroke width in
    every direction, so half-width is added on all four sides rather than only
    where the path is axis-parallel.
    """
    half = STROKE_W / 2
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    for p0, p1, p2, p3 in CURVES:
        for i in range(401):
            t = i / 400
            u = 1 - t
            x = u**3*p0[0] + 3*u**2*t*p1[0] + 3*u*t**2*p2[0] + t**3*p3[0]
            y = u**3*p0[1] + 3*u**2*t*p1[1] + 3*u*t**2*p2[1] + t**3*p3[1]
            x0, x1 = min(x0, x - half), max(x1, x + half)
            y0, y1 = min(y0, y - half), max(y1, y + half)
    return x0 + dx, y0 + dy, x1 + dx, y1 + dy


def union(*boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def mark_svg(stroke):
    """The mark as SVG elements, in the 64x64 design box."""
    d = " ".join(
        f"M {c[0][0]} {c[0][1]} C {c[1][0]} {c[1][1]}, {c[2][0]} {c[2][1]}, {c[3][0]} {c[3][1]}"
        if i == 0 else
        f"C {c[1][0]} {c[1][1]}, {c[2][0]} {c[2][1]}, {c[3][0]} {c[3][1]}"
        for i, c in enumerate(CURVES)
    )
    return [f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{STROKE_W}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>']


def wordmark_svg(x, baseline1, baseline2, fill, centre_width=None):
    """Outlined wordmark. If centre_width is given, centre both lines in it."""
    scale = TEXT_SIZE / _upem
    p1, w1 = glyph_run(LINE1, TEXT_SIZE, TRACKING)
    p2, w2 = glyph_run(LINE2, TEXT_SIZE, TRACKING)
    out = []
    for parts, w, base in ((p1, w1, baseline1), (p2, w2, baseline2)):
        tx = x + (centre_width - w) / 2 if centre_width is not None else x
        out.append(f'<g fill="{fill}" transform="translate({tx:.2f} {base}) '
                   f'scale({scale:.6f} -{scale:.6f})">')
        out.extend("  " + p for p in parts)
        out.append("</g>")
    return out, max(w1, w2)


def svg_doc(bbox, body, title):
    """Tight-cropped SVG: the viewBox IS the ink bounding box, so the asset has
    no baked-in padding and drops into a layout dead-centre. Clear space is
    applied by the person placing it (see brand/README.md)."""
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="{x0:.3f} {y0:.3f} {w:.3f} {h:.3f}" '
            f'width="{w:.3f}" height="{h:.3f}" role="img" aria-label="{title}">\n'
            f"  <title>{title}</title>\n"
            + "\n".join("  " + line for line in body)
            + "\n</svg>\n")


# ── the four colourways ───────────────────────────────────────────────────
# (name, mark stroke, wordmark). The mark is a single stroke now, so a
# colourway is two colours at most.
WAYS = [
    ("colour", COPPER, NAVY),
    ("navy", NAVY, NAVY),
    ("black", BLACK, BLACK),
    ("white", WHITE, WHITE),
]


GAP = 16.0          # mark-to-wordmark gap in the horizontal lockup, ink to ink
STACK_GAP = 20.0    # mark-to-wordmark gap in the stacked lockup, ink to ink


def build_mark(name, stroke, _word):
    bbox = mark_bbox()
    return svg_doc(bbox, mark_svg(stroke), "Southern AI Consulting mark"), bbox


def build_horizontal(name, stroke, word):
    # Measured from the mark's right-hand ink edge, not from the 64-unit design
    # box, so GAP is the gap you actually see.
    tx = mark_bbox()[2] + GAP
    # Baselines chosen so the wordmark's cap-to-baseline block (14.45 -> 49.6,
    # centre 32.03) sits on the mark's centre line at y=32.
    b1, b2 = 27.6, 49.6
    body = mark_svg(stroke)
    wm, _ = wordmark_svg(tx, b1, b2, word)
    body += wm
    bbox = union(mark_bbox(),
                 text_bbox(tx, b1, LINE1),
                 text_bbox(tx, b2, LINE2))
    return svg_doc(bbox, body, "Southern AI Consulting"), bbox


def build_stacked(name, stroke, word):
    mb = mark_bbox()
    _, wmw = wordmark_svg(0, 0, 0, word)
    mark_ink_w = mb[2] - mb[0]
    width = max(mark_ink_w, wmw)
    # centre the mark's INK (not its 64-unit box) over the wordmark
    mark_dx = (width - mark_ink_w) / 2 - mb[0]
    b1 = mb[3] + STACK_GAP + 13.2          # +cap height, so the gap is ink-to-ink
    b2 = b1 + 22.0
    body = [f'<g transform="translate({mark_dx:.3f} 0)">']
    body += ["  " + s for s in mark_svg(stroke)]
    body.append("</g>")
    wm, _ = wordmark_svg(0, b1, b2, word, centre_width=width)
    body += wm
    bbox = union(mark_bbox(dx=mark_dx),
                 text_bbox((width - text_width(LINE1)) / 2, b1, LINE1),
                 text_bbox((width - text_width(LINE2)) / 2, b2, LINE2))
    return svg_doc(bbox, body, "Southern AI Consulting"), bbox


BUILDERS = {
    "logo-mark": build_mark,
    "logo-horizontal": build_horizontal,
    "logo-stacked": build_stacked,
}


# ── PNG: PIL raster (font is baked into pixels, so no font dependency) ────
def png_mark(d, ox, oy, s, stroke):
    def px(p):
        return (ox + p[0] * s, oy + p[1] * s)

    brush = STROKE_W * s / 2
    for p0, p1, p2, p3 in CURVES:
        for i in range(1201):
            t = i / 1200
            u = 1 - t
            x = u**3*p0[0] + 3*u**2*t*p1[0] + 3*u*t**2*p2[0] + t**3*p3[0]
            y = u**3*p0[1] + 3*u**2*t*p1[1] + 3*u*t**2*p2[1] + t**3*p3[1]
            cx, cy = px((x, y))
            d.ellipse([cx-brush, cy-brush, cx+brush, cy+brush], fill=stroke)


def tracked(d, xy, text, font, fill, track):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + track


def render_png(kind, name, stroke, word, target_w, path, bbox):
    """Raster the same geometry, cropped to the same tight bbox as the SVG.
    The wordmark is drawn with the real font here; because the output is
    pixels there is no font dependency downstream."""
    SS = 4
    x0, y0, x1, y1 = bbox
    unit_w, unit_h = x1 - x0, y1 - y0
    s = target_w * SS / unit_w
    W, H = int(round(unit_w * s)), int(round(unit_h * s))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # translate so the bbox origin lands at (0,0)
    ox, oy = -x0 * s, -y0 * s

    if kind == "logo-mark":
        png_mark(d, ox, oy, s, stroke)
    else:
        f = ImageFont.truetype(GEORGIA_BOLD, max(1, int(round(TEXT_SIZE * s))))
        asc, _ = f.getmetrics()   # PIL draws from the text top, not the baseline
        if kind == "logo-horizontal":
            png_mark(d, ox, oy, s, stroke)
            # Same ink-relative offset and baselines as build_horizontal().
            tx = ox + (mark_bbox()[2] + GAP) * s
            tracked(d, (tx, oy + 27.6*s - asc), LINE1, f, word, TRACKING*s)
            tracked(d, (tx, oy + 49.6*s - asc), LINE2, f, word, TRACKING*s)
        else:
            mb = mark_bbox()
            mark_ink_w = mb[2] - mb[0]
            width = max(mark_ink_w, text_width(LINE1), text_width(LINE2))
            mark_dx = (width - mark_ink_w) / 2 - mb[0]
            b1 = mb[3] + STACK_GAP + 13.2
            b2 = b1 + 22.0
            png_mark(d, ox + mark_dx*s, oy, s, stroke)
            for line, base in ((LINE1, b1), (LINE2, b2)):
                lw = sum(d.textlength(c, font=f) + TRACKING*s for c in line) - TRACKING*s
                tracked(d, (ox + (width*s - lw)/2, oy + base*s - asc),
                        line, f, word, TRACKING*s)
    img.resize((max(1, W//SS), max(1, H//SS)), Image.LANCZOS).save(
        path, "PNG", optimize=True)
    return W//SS, H//SS


def main():
    os.makedirs(OUT, exist_ok=True)
    made = []
    for kind, builder in BUILDERS.items():
        bbox = None
        for name, stroke, word in WAYS:
            svg, bbox = builder(name, stroke, word)
            p = f"{OUT}/{kind}-{name}.svg"
            open(p, "w").write(svg)
            made.append(f"{p}  [{bbox[2]-bbox[0]:.1f} x {bbox[3]-bbox[1]:.1f} units]")
        # 300 dpi PNGs: 2 inch and 4 inch wide, colour + reverse only
        for name, stroke, word in WAYS:
            if name not in ("colour", "white"):
                continue
            for inches in (2, 4):
                p = f"{OUT}/{kind}-{name}-{inches}in-300dpi.png"
                w, h = render_png(kind, name, stroke, word,
                                  inches * 300, p, bbox)
                made.append(f"{p} ({w}x{h}px)")
    for m in made:
        print(" ", m)
    print(f"\n{len(made)} files written to {OUT}/")


if __name__ == "__main__":
    main()
