#!/usr/bin/env python3
"""Generate the site's two raster images:

  og.png                1200x630 social/link-preview card
  apple-touch-icon.png  180x180 home-screen icon

Regenerate after any brand change:   python3 tools/make_og.py
Requires Pillow and the Georgia font (present by default on macOS).

Pillow does not antialias shape drawing, so everything is rendered at SS x
scale and downsampled with LANCZOS. The mark itself is a polygon straight out
of tools/mark_geometry.py — no rasteriser-specific drawing of its own, so it
cannot drift from the SVGs.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont

from markutil import BADGE_FILL, mark_draw
from mark_geometry import MARK_H, MARK_W

W, H = 1200, 630
# Supersample factor. Pillow does not antialias polygon fills at all, and the
# mark is curves from end to end.
SS = 4

NAVY = "#10233A"
COPPER = "#D99A6C"
CREAM = "#FBF9F6"
SLATE = "#9FB0C0"

GEORGIA = "/System/Library/Fonts/Supplemental/Georgia.ttf"
GEORGIA_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"

# The mark, from tools/mark_geometry.py. Ink is tight to a MARK_W x MARK_H box.
# 316 px of ink tall, vertically centred in the 630 px card, leaving air before
# the text column at x=390. At that size the circuit is wide open — this is the
# one place the mark is ever seen big, so it gets the full drawing.
#
# Reversed, the mark takes the lifted copper rather than the cream. The card's
# wordmark is already cream and is by far the biggest thing on it; a cream mark
# beside it reads as another line of the same text block, where copper reads as
# the logo. It is also the only warm note on a navy field. The circuit is a
# hole, so it simply shows the card's own navy — no third colour involved.
MARK_INK_H = 316
SCALE = MARK_INK_H / MARK_H
OX = 68
OY = (H - MARK_INK_H) / 2


def tracked_text(draw, xy, text, font, fill, tracking):
    """Pillow has no letter-spacing, so advance manually."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking


TOUCH = 180             # iOS home-screen icon, the one size modern iOS asks for


def touch_icon():
    """apple-touch-icon.png — the badge, but as pixels and full bleed.

    iOS will not take an SVG here, which is why favicon.svg cannot serve double
    duty however tempting the single file is. It also masks the corners itself,
    so this ships as a plain square: round them here as well and the two
    roundings fight and the edge goes ragged.

    Unlike favicon.svg this one DOES get the circuit. That file has to survive a
    16 px browser tab; this is only ever drawn at 180, where the channel is
    seven pixels wide and the detail is the whole point.
    """
    img = Image.new("RGB", (TOUCH * SS, TOUCH * SS), NAVY)
    s = BADGE_FILL * TOUCH / MARK_H
    ox, oy = (TOUCH - MARK_W * s) / 2, (TOUCH - MARK_H * s) / 2
    mark_draw(ImageDraw.Draw(img), ox * SS, oy * SS, s * SS, COPPER, NAVY)
    img.resize((TOUCH, TOUCH), Image.LANCZOS).save(
        "apple-touch-icon.png", "PNG", optimize=True)
    print(f"wrote apple-touch-icon.png ({TOUCH}x{TOUCH}, "
          f"{BADGE_FILL * TOUCH:.0f}px of ink)")


def main():
    img = Image.new("RGB", (W * SS, H * SS), NAVY)
    d = ImageDraw.Draw(img)

    mark_draw(d, OX * SS, OY * SS, SCALE * SS, COPPER, NAVY)

    # Text column. Font sizes and coordinates are in final pixels, x SS.
    x = 390 * SS
    f_eyebrow = ImageFont.truetype(GEORGIA_BOLD, 21 * SS)
    f_brand = ImageFont.truetype(GEORGIA_BOLD, 74 * SS)
    f_tag = ImageFont.truetype(GEORGIA, 33 * SS)

    tracked_text(d, (x, 150 * SS), "PRATTVILLE  ·  MONTGOMERY  ·  BIRMINGHAM",
                 f_eyebrow, SLATE, 2.4 * SS)

    d.text((x, 196 * SS), "Southern AI", font=f_brand, fill=CREAM)
    d.text((x, 286 * SS), "Consulting", font=f_brand, fill=CREAM)

    d.line([(x + 3 * SS, 404 * SS), (x + 93 * SS, 404 * SS)],
           fill=COPPER, width=4 * SS)

    d.text((x, 432 * SS), "AI that takes the busywork", font=f_tag, fill=COPPER)
    d.text((x, 476 * SS), "off your desk.", font=f_tag, fill=COPPER)

    img = img.resize((W, H), Image.LANCZOS)
    img.save("og.png", "PNG", optimize=True)
    print(f"wrote og.png ({W}x{H})")
    touch_icon()


if __name__ == "__main__":
    main()
