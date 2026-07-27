#!/usr/bin/env python3
"""The two-line Georgia Bold wordmark: measuring and outlining.

Shared by make_site_svgs.py and make_brand_assets.py so the lockup geometry
is defined once. Outlining matters for print: a vendor without Georgia
silently substitutes another face, and the logo comes back wrong.
"""

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

GEORGIA_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"

LINE1, LINE2 = "SOUTHERN AI", "CONSULTING"
TEXT_SIZE = 19.0
TRACKING = 0.6          # px of extra letter-spacing at TEXT_SIZE

# Baselines that put the wordmark's cap-to-baseline block (14.45 -> 49.6,
# centre 32.03) on the centre line of a 64-unit-tall mark.
BASE1, BASE2 = 27.6, 49.6

# How the mark sits beside the words. BOTH lockup builders read these, because
# they have already disagreed once: the site file drew the mark at its full 64
# units while the print set used 48, so an email signature and a business card
# carried the same logo at 1.82 and 1.37 times the wordmark. Constants that
# describe one drawing belong in one place.
GAP = 16.0              # mark-to-wordmark gap, ink to ink
LOCKUP_MARK_H = 48.0    # mark ink height beside the wordmark

# At its full 64 the mark stands 1.8x the wordmark's 35-unit cap block and
# reads as a mark with some words parked beside it; 48 keeps the 1.35 ratio
# the lockup was drawn to. The mark on its own is always full size — this is a
# lockup rule, not a size for the mark.

_font = TTFont(GEORGIA_BOLD)
_glyphs = _font.getGlyphSet()
_cmap = _font.getBestCmap()
_upem = _font["head"].unitsPerEm


def glyph_run(text, size=TEXT_SIZE, tracking=TRACKING):
    """Outline `text` as SVG path fragments plus its advance width in px.

    Fragments are in font units; the caller wraps them in a transform that
    scales by size/upem and flips Y (fonts are Y-up, SVG is Y-down).
    """
    scale = size / _upem
    track_units = tracking / scale
    x, parts = 0.0, []
    for ch in text:
        pen = SVGPathPen(_glyphs)
        _glyphs[_cmap[ord(ch)]].draw(pen)
        d = pen.getCommands()
        if d:
            parts.append(f'<path transform="translate({x:.2f} 0)" d="{d}"/>')
        x += _glyphs[_cmap[ord(ch)]].width + track_units
    return parts, ((x - track_units) * scale if text else 0.0)


def text_width(text, tracking=TRACKING):
    return glyph_run(text, TEXT_SIZE, tracking)[1]


def text_bbox(x, baseline, text, tracking=TRACKING):
    """Exact ink bounds of a run, in px, y-down like SVG."""
    scale = TEXT_SIZE / _upem
    track_units = tracking / scale
    pen_x = 0.0
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    for ch in text:
        bp = BoundsPen(_glyphs)
        _glyphs[_cmap[ord(ch)]].draw(bp)
        if bp.bounds:
            gx0, gy0, gx1, gy1 = bp.bounds
            x0 = min(x0, x + (pen_x + gx0) * scale)
            x1 = max(x1, x + (pen_x + gx1) * scale)
            y0 = min(y0, baseline - gy1 * scale)   # font y-up -> SVG y-down
            y1 = max(y1, baseline - gy0 * scale)
        pen_x += _glyphs[_cmap[ord(ch)]].width + track_units
    return x0, y0, x1, y1


def wordmark_svg(x, baseline1, baseline2, fill, centre_width=None):
    """Outlined wordmark. If centre_width is given, centre both lines in it."""
    scale = TEXT_SIZE / _upem
    p1, w1 = glyph_run(LINE1)
    p2, w2 = glyph_run(LINE2)
    out = []
    for parts, w, base in ((p1, w1, baseline1), (p2, w2, baseline2)):
        tx = x + (centre_width - w) / 2 if centre_width is not None else x
        out.append(f'<g fill="{fill}" transform="translate({tx:.2f} {base}) '
                   f'scale({scale:.6f} -{scale:.6f})">')
        out.extend("  " + p for p in parts)
        out.append("</g>")
    return out, max(w1, w2)
