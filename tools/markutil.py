#!/usr/bin/env python3
"""Shared helpers for building assets out of tools/mark_geometry.py.

Everything that draws the mark goes through here so the SVG files, the PNGs
and the OG card can never disagree about what the logo is.

The mark is ONE PATH IN ONE COLOUR. The circuit running through it is a hole,
not a second ink — MARK_PATH and CIRCUIT_PATH go into the same `d` under
fill-rule="evenodd", the letter fills, the channel and node discs inside it do
not, and the five dots inside those do again. So there is never a background
colour to pass in and never a second plate to drop.
"""

from mark_geometry import (MARK_PATH, MARK_POLY, MARK_W, MARK_H,
                           CIRCUIT_PATH, RIBBON_POLY, NODES, HOLE_R,
                           SOLID_BELOW_PX)

NAVY = "#10233A"
COPPER = "#B26B3F"
CREAM = "#FBF9F6"
BLACK = "#000000"
WHITE = "#FFFFFF"
# Copper is only 1.9:1 against navy and goes muddy small, so reversed artwork
# uses a lifted copper instead of the flat brand value.
COPPER_ON_DARK = "#D99A6C"

# Ink height as a fraction of a badge tile — favicon.svg and apple-touch-icon
# both read it, so the two cannot end up at different sizes. Measured: fill
# fractions 0.62 to 0.78 compared at 16, 20, 24, 32 and 48 px. The letter's
# widest points sit at mid-height on the left and right edges, nowhere near the
# tile's rounded corners, which is what lets it run larger here than a mark
# with corners could; 0.78 is still too much, the bowls come within a couple of
# pixels of the edge at 48 px and it reads cramped rather than confident.
BADGE_FILL = 0.74


def mark_path(circuit=True):
    return MARK_PATH + " " + CIRCUIT_PATH if circuit else MARK_PATH


def mark_svg(colour, circuit=True, indent="  "):
    """The mark as ONE SVG element in the MARK_W x MARK_H design box.

    `circuit=False` is the reduction: the letter alone, for anything below
    SOLID_BELOW_PX of ink. It is the same drawing with one thing left off, not
    a second artwork — that is the whole point of building it this way.
    """
    rule = ' fill-rule="evenodd"' if circuit else ""
    return [f'{indent}<path d="{mark_path(circuit)}"{rule} fill="{colour}"/>']


def mark_bbox(dx=0.0, dy=0.0):
    """Ink bounds. The geometry is generated tight to its box, so this is the
    box — but go through the outline anyway, so a future change to how the box
    is derived cannot silently break every lockup's alignment. The circuit is
    strictly inside the letter, so it never affects this."""
    xs = [p[0] for p in MARK_POLY]
    ys = [p[1] for p in MARK_POLY]
    return min(xs) + dx, min(ys) + dy, max(xs) + dx, max(ys) + dy


# ── raster ────────────────────────────────────────────────────────────────


def mark_draw(draw, ox, oy, s, ink, back=None):
    """Draw the mark with Pillow at scale s, origin (ox, oy).

    Pillow has no even-odd fill and no way to put a hole in a polygon, so the
    same region is reached by painting: letter, channel back out in `back`,
    then the dots on top again. Pass back=None for the solid reduction.

    Uses the pre-flattened MARK_POLY / RIBBON_POLY rather than the path data:
    Pillow cannot draw a curve, and flattening belongs next to the curve that
    produced it, in design_mark.py, not here.
    """
    P = lambda pts: [(ox + x * s, oy + y * s) for x, y in pts]
    draw.polygon(P(MARK_POLY), fill=ink)
    if back is None:
        return
    draw.polygon(P(RIBBON_POLY), fill=back)
    for x, y in NODES:
        cx, cy, r = ox + x * s, oy + y * s, HOLE_R * s
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ink)


def mark_mask(size, ox, oy, s, circuit=True):
    """The mark's coverage as an L-mode image: 255 is ink, 0 is not.

    Colour is applied after the mask has been downsampled, never before. PIL
    does not premultiply, so resampling an RGBA image pulls the colour channels
    of every edge pixel towards whatever is sitting in the transparent areas,
    and the mark comes back with a dark halo round it — with a knockout, a halo
    down the middle of the letter as well. Resample the coverage instead and
    colour it afterwards and there is nothing for it to average against.
    """
    from PIL import Image, ImageDraw
    m = Image.new("L", size, 0)
    mark_draw(ImageDraw.Draw(m), ox, oy, s, 255, 0 if circuit else None)
    return m


def colourise(size, *layers):
    """Stack (mask, "#rrggbb") pairs into a straight-alpha RGBA image."""
    from PIL import Image
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    for mask, colour in layers:
        c = colour.lstrip("#")
        lay = Image.new("RGBA", size,
                        tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
        lay.putalpha(mask)
        out.alpha_composite(lay)
    return out
