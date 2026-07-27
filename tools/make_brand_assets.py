#!/usr/bin/env python3
"""Generate the print-ready brand asset set into brand/.

    python3 tools/make_brand_assets.py

Run tools/design_mark.py first if the letterform itself changed.

Why this script exists: logo-lockup.svg uses a live <text> element in Georgia.
A print shop without Georgia silently substitutes another face and the logo is
wrong on the finished cards. Everything produced here has the wordmark
converted to real vector outlines via fontTools, so there is no font
dependency at any point in the print chain.

Outputs (brand/):
  logo-mark-{colour,navy,black,white}.svg        mark alone
  logo-mark-solid-{...}.svg                      ... without the circuit
  logo-horizontal-{colour,navy,black,white}.svg  mark + wordmark, side by side
  logo-stacked-{colour,navy,black,white}.svg     mark above wordmark
  *.png                                          300 dpi, transparent

The circuit inside the mark is a HOLE, so every file here works on any stock
without knowing what colour it is — and the artwork stays one ink, so a
one-plate job loses nothing. The `-solid` marks are for processes that cannot
hold a hole at all: embroidery, a rubber stamp, engraving.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont

import wordmark as wm
from markutil import (NAVY, COPPER, BLACK, WHITE, colourise, mark_bbox,
                      mark_draw, mark_svg)

OUT = "brand"

# (name, mark, wordmark). The mark itself is a single ink in every colourway;
# only the primary one sets the wordmark in a different colour from the mark.
WAYS = [
    ("colour", COPPER, NAVY),
    ("navy", NAVY, NAVY),
    ("black", BLACK, BLACK),
    ("white", WHITE, WHITE),
]

# The horizontal lockup's two numbers live in wordmark.py, because
# make_site_svgs.py builds the same lockup and the two used to disagree.
GAP, LOCKUP_MARK_H = wm.GAP, wm.LOCKUP_MARK_H

STACK_GAP = 20.0    # mark-to-wordmark gap in the stacked lockup, ink to ink
CAP_H = 13.2        # Georgia Bold cap height at TEXT_SIZE, for the stacked gap

# The stacked lockup needs its own, larger size. The mark sits above a text
# block nearly three times its width, and at the horizontal lockup's 48 units
# it reads as an afterthought floating over the words.
STACK_MARK_H = 58.0

MARK_S = LOCKUP_MARK_H / mark_bbox()[3]
MARK_DY = (64.0 - LOCKUP_MARK_H) / 2      # centre it on the 64-unit centre line


def mark_scale(mark_h):
    """(scale, dy) placing `mark_h` units of ink on the 64-unit centre line."""
    return mark_h / mark_bbox()[3], (64.0 - mark_h) / 2


def placed_mark(mark, dx=0.0, mark_h=LOCKUP_MARK_H, circuit=True):
    """The mark at lockup scale, and the ink bbox it occupies."""
    s, dy = mark_scale(mark_h)
    body = [f'<g transform="translate({dx:.3f} {dy:.3f}) scale({s:.5f})">']
    body += ["  " + line for line in mark_svg(mark, circuit, indent="")]
    body.append("</g>")
    x0, y0, x1, y1 = mark_bbox()
    return body, (x0 * s + dx, y0 * s + dy, x1 * s + dx, y1 * s + dy)


def union(*boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


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


def build_mark(mark, _word, circuit=True):
    bbox = mark_bbox()
    return svg_doc(bbox, mark_svg(mark, circuit, indent=""),
                   "Southern AI Consulting mark"), bbox


def build_mark_solid(mark, word):
    """The reduction: the letter with the circuit left off, for anything that
    cannot hold a hole — embroidery, a rubber stamp, an engraving. It is the
    same drawing minus one thing, not a redraw."""
    return build_mark(mark, word, circuit=False)


def build_horizontal(mark, word):
    # Measured from the mark's right-hand ink edge, so GAP is the gap you
    # actually see.
    body, mb = placed_mark(mark)
    tx = mb[2] + GAP
    body += wordmark_lines(tx, word)
    bbox = union(mb,
                 wm.text_bbox(tx, wm.BASE1, wm.LINE1),
                 wm.text_bbox(tx, wm.BASE2, wm.LINE2))
    return svg_doc(bbox, body, "Southern AI Consulting"), bbox


def wordmark_lines(tx, word, centre_width=None):
    return wm.wordmark_svg(tx, wm.BASE1, wm.BASE2, word, centre_width)[0]


def build_stacked(mark, word):
    _, mb0 = placed_mark(mark, mark_h=STACK_MARK_H)
    wmw = max(wm.text_width(wm.LINE1), wm.text_width(wm.LINE2))
    mark_ink_w = mb0[2] - mb0[0]
    width = max(mark_ink_w, wmw)
    # centre the mark's INK over the wordmark
    body, mb = placed_mark(mark, dx=(width - mark_ink_w) / 2 - mb0[0],
                           mark_h=STACK_MARK_H)
    b1 = mb[3] + STACK_GAP + CAP_H          # +cap height, so the gap is ink-to-ink
    b2 = b1 + 22.0
    body += wm.wordmark_svg(0, b1, b2, word, centre_width=width)[0]
    bbox = union(mb,
                 wm.text_bbox((width - wm.text_width(wm.LINE1)) / 2, b1, wm.LINE1),
                 wm.text_bbox((width - wm.text_width(wm.LINE2)) / 2, b2, wm.LINE2))
    return svg_doc(bbox, body, "Southern AI Consulting"), bbox


BUILDERS = {
    "logo-mark": build_mark,
    "logo-mark-solid": build_mark_solid,
    "logo-horizontal": build_horizontal,
    "logo-stacked": build_stacked,
}

# Which kinds also get 300 dpi rasters, and in which colourways. The solid mark
# is a vector-only deliverable — the shops that need it (embroidery digitisers,
# stamp makers, engravers) all want an outline, not pixels.
RASTERED = ("logo-mark", "logo-horizontal", "logo-stacked")


# ── PNG: PIL raster (font is baked into pixels, so no font dependency) ────


def tracked(d, xy, text, font, fill, track):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + track


def render_png(kind, mark, word, target_w, path, bbox):
    """Raster the same geometry, cropped to the same tight bbox as the SVG.

    The mark and the wordmark are drawn as COVERAGE MASKS and coloured only
    after they have been downsampled. PIL does not premultiply alpha, so
    resampling a coloured RGBA image drags the colour channels of every edge
    pixel towards the transparent background and the artwork comes back with a
    dark halo — right down the middle of the letter, now that the circuit is a
    hole. Colouring flat masks afterwards leaves nothing to average against.

    The wordmark is drawn with the real font; because the output is pixels
    there is no font dependency downstream.
    """
    SS = 4
    x0, y0, x1, y1 = bbox
    unit_w, unit_h = x1 - x0, y1 - y0
    s = target_w * SS / unit_w
    W, H = int(round(unit_w * s)), int(round(unit_h * s))
    ox, oy = -x0 * s, -y0 * s      # translate so the bbox origin lands at (0,0)
    ink, type_ = Image.new("L", (W, H), 0), Image.new("L", (W, H), 0)
    d, t = ImageDraw.Draw(ink), ImageDraw.Draw(type_)

    if kind == "logo-mark":
        mark_draw(d, ox, oy, s, 255, 0)
    else:
        f = ImageFont.truetype(wm.GEORGIA_BOLD, max(1, int(round(wm.TEXT_SIZE * s))))
        asc, _ = f.getmetrics()   # PIL draws from the text top, not the baseline
        if kind == "logo-horizontal":
            mark_draw(d, ox, oy + MARK_DY * s, s * MARK_S, 255, 0)
            tx = ox + (mark_bbox()[2] * MARK_S + GAP) * s
            for line, base in ((wm.LINE1, wm.BASE1), (wm.LINE2, wm.BASE2)):
                tracked(t, (tx, oy + base * s - asc), line, f, 255, wm.TRACKING * s)
        else:
            ms, mdy = mark_scale(STACK_MARK_H)   # stacked uses the larger mark
            x0, _, x1, y1 = mark_bbox()
            mark_ink_w = (x1 - x0) * ms
            width = max(mark_ink_w, wm.text_width(wm.LINE1), wm.text_width(wm.LINE2))
            mark_dx = (width - mark_ink_w) / 2 - x0 * ms
            b1 = y1 * ms + mdy + STACK_GAP + CAP_H
            b2 = b1 + 22.0
            mark_draw(d, ox + mark_dx * s, oy + mdy * s, s * ms, 255, 0)
            for line, base in ((wm.LINE1, b1), (wm.LINE2, b2)):
                lw = sum(t.textlength(c, font=f) + wm.TRACKING * s for c in line) \
                    - wm.TRACKING * s
                tracked(t, (ox + (width * s - lw) / 2, oy + base * s - asc),
                        line, f, 255, wm.TRACKING * s)

    fin = (max(1, W // SS), max(1, H // SS))
    colourise(fin, (ink.resize(fin, Image.LANCZOS), mark),
              (type_.resize(fin, Image.LANCZOS), word)).save(
        path, "PNG", optimize=True)
    return fin


def main():
    os.makedirs(OUT, exist_ok=True)
    made = []
    for kind, builder in BUILDERS.items():
        bbox = None
        for name, mark, word in WAYS:
            svg, bbox = builder(mark, word)
            p = f"{OUT}/{kind}-{name}.svg"
            open(p, "w").write(svg)
            made.append(f"{p}  [{bbox[2]-bbox[0]:.1f} x {bbox[3]-bbox[1]:.1f} units]")
        # 300 dpi PNGs: 2 inch and 4 inch wide, colour + reverse only
        for name, mark, word in WAYS:
            if kind not in RASTERED or name not in ("colour", "white"):
                continue
            for inches in (2, 4):
                p = f"{OUT}/{kind}-{name}-{inches}in-300dpi.png"
                w, h = render_png(kind, mark, word, inches * 300, p, bbox)
                made.append(f"{p} ({w}x{h}px)")
    for m in made:
        print(" ", m)
    print(f"\n{len(made)} files written to {OUT}/")


if __name__ == "__main__":
    main()
