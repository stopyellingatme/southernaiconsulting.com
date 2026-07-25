#!/usr/bin/env python3
"""Generate og.png (1200x630) — the social/link-preview card.

Regenerate after any brand change:   python3 tools/make_og.py
Requires Pillow and the Georgia font (present by default on macOS).

Two implementation notes worth keeping:
  * Pillow's draw.line(joint="curve") leaves visible seams on very thick
    strokes, so the curve is brush-stamped instead — a filled circle at every
    sampled point, which also gives free round caps.
  * Pillow does not antialias shape drawing, so everything is rendered at
    SS x scale and downsampled with LANCZOS.
"""

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
SS = 3  # supersample factor

NAVY = "#10233A"
COPPER = "#D99A6C"
CREAM = "#FBF9F6"
SLATE = "#9FB0C0"

GEORGIA = "/System/Library/Fonts/Supplemental/Georgia.ttf"
GEORGIA_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"

# Mark geometry, identical to logo.svg (viewBox 0 0 64 64).
CURVES = [
    ((44, 12), (24, 12), (24, 30), (32, 32)),
    ((32, 32), (40, 34), (40, 52), (20, 52)),
]
NODES = [(44, 12), (32, 32), (20, 52)]

STROKE_W = 5.5   # in viewBox units, matches logo.svg
NODE_R = 3.6     # in viewBox units, matches logo.svg
SCALE = 6.5
OX, OY = -8, 107


def to_px(pt):
    """viewBox units -> supersampled device pixels."""
    x, y = pt
    return ((OX + x * SCALE) * SS, (OY + y * SCALE) * SS)


def cubic(p0, p1, p2, p3, steps=700):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append(to_px((x, y)))
    return pts


def stamp(draw, pts, radius, fill):
    """Brush-stamp a circle at each point: seamless stroke with round caps."""
    for cx, cy in pts:
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=fill)


def dot(draw, pt, radius, fill):
    cx, cy = to_px(pt)
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=fill)


def tracked_text(draw, xy, text, font, fill, tracking):
    """Pillow has no letter-spacing, so advance manually."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking


def main():
    img = Image.new("RGB", (W * SS, H * SS), NAVY)
    d = ImageDraw.Draw(img)

    brush = STROKE_W * SCALE * SS / 2
    for curve in CURVES:
        stamp(d, cubic(*curve), brush, COPPER)

    node_r = NODE_R * SCALE * SS
    for pt in NODES:
        dot(d, pt, node_r, CREAM)

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


if __name__ == "__main__":
    main()
