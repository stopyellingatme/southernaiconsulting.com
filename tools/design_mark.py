#!/usr/bin/env python3
"""Draw the S mark and write tools/mark_geometry.py.

    python3 tools/design_mark.py

You only need to run this if you are changing the LETTERFORM itself. Everything
else in the repo reads the generated tools/mark_geometry.py, so the day-to-day
asset build is fast and has no dependencies at all.

How the letter is built
-----------------------
The S is a stroked spine, and the spine is 270 degrees of ONE ELLIPSE followed
by its own 180-degree rotation about the point where that arc ends. Rotating
about the END means the second bowl starts where the first stopped, travelling
the same way, whatever the sweep is — so the join is C1 for free and there is
no waist to match up by hand. (Rotating about the origin gives the same answer
at 270 degrees, because that is where the arc happens to finish, and tears the
letter open at any other sweep without tripping a single check in this file.
CENTRE is derived for that reason.)

That one arc produces everything. The outer edge, both counters and both
terminals are the spine pushed out by a width function, and the whole lower
half of the letter is the upper half negated. Only half the S is ever
described, so it cannot go out of symmetry.

Six numbers make the letterform — RX, RY, the mean half stroke, its swell on
the verticals, the sweep, and where the terminals are cut. Everything else is
derived.

The stroke is a modulated monoline: h(t) = HM + HS*cos(2t). It runs thin where
the stroke is horizontal (the tops and bottoms of the bowls) and thick where it
is vertical, which is the ordinary contrast of a grotesque and is what stops a
constant-width S reading as a bent pipe.

The circuit
-----------
The trace is the SAME SPINE drawn thin. That is the whole trick: it is not a
second drawing laid on top and nudged into place, so it cannot drift off the
letter at any size or under any transform, and the nodes sit on it at fixed
angles. Five nodes cost two numbers, because three of them are the other two
rotated plus the join itself.

The circuit is a KNOCKOUT, not a second ink. The channel and the node rings
show whatever is behind the mark — the page, the tile, the paper. So the mark
is still one ink everywhere, one-plate printing loses nothing, and on the site
the two tones follow the light/dark theme automatically because the second
"colour" is just var(--bg).

Below about 32 px of ink the trace closes up. That is what SOLID_BELOW_PX
records, and it is why favicon.svg and the small-screen header drop the circuit
layer — not by switching to a different drawing, but by not drawing one layer
of this one. The reduction is the letter itself.

Where the numbers came from
---------------------------
They were fitted by least squares to the reference artwork's antialiased
coverage, not eyeballed: 0.957 silhouette overlap. The reference's own medial
axis is what gave away the ellipse — every ridge point of its distance
transform sits on it to within about 2%.
"""

import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mark_geometry.py")

# ── the letterform ────────────────────────────────────────────────────────
# In the reference raster's own pixels. The whole drawing is scaled once at the
# end so the ink stands exactly BOX_H tall, so only the RATIOS here matter.
RX, RY = 21.35, 18.00   # the spine ellipse: half width, half height
HM, HS = 11.00, 1.15    # half the stroke: mean, and its swell on the verticals
SWEEP = 270.0           # degrees of the ellipse each bowl runs
CUT = 0.70              # terminals cut this far past the bowl's own axis
T0 = 10.0               # where sampling starts; the trim throws away the
                        # overshoot, it just has to begin below the cut

BOX_H = 64.0            # design box height in output units; ink is tight to it

# Where the first bowl's arc ends, which is the letter's centre and the point
# the second bowl is the first one turned about. At SWEEP=270 this is the
# origin and the rotation is a plain negation — but deriving it means SWEEP is
# genuinely free: nudge it and the two halves still meet. Left as a negation it
# would tear the letter open at the waist by 2*|CENTRE| and every trip wire in
# this file would still pass, because a torn outline is a perfectly valid one.
CENTRE = (RX * math.cos(math.radians(-SWEEP)),
          -RY + RY * math.sin(math.radians(-SWEEP)))

# ── the circuit ───────────────────────────────────────────────────────────
# Two angles on the spine, measured off the reference. The other two nodes are
# these rotated, and the fifth is the join at the letter's centre.
NODE_T = (-34.24, -164.11)
TRACE_W = 3.70          # channel width, in reference pixels
NODE_R = 4.60           # node ring, outer radius
HOLE_R = 1.95           # the ink dot left in the middle of a node

# Measured on a true 1x ladder (64, 48, 40, 32, 26, 22, 18, 14, 11, 9, 7 px of
# ink): the trace is crisp to 32, soft at 26 and closed by 22. The letter under
# it holds to 7. Anything placed smaller than this gets circuit=False.
SOLID_BELOW_PX = 32

# Sampling and flattening. FLATTEN_TOL is in output units: the largest raster
# we ship is a 4 in 300 dpi mark rendered 4x supersampled, where one unit is
# about 103 px, so 0.01 is a quarter of a pixel in the finished file.
SAMPLES = 240           # spine samples per bowl before fitting
FIT_TOL = 0.02          # how far the shipped cubics may stray from the true
                        # geometry, in output units: 0.03% of the height, or
                        # 0.4 px on the largest raster we ship
FLATTEN_TOL = 0.01      # and how far the polygon may stray from those cubics
POLY_EPS = 0.005        # half a unit in the last decimal the polygons are
                        # written at, so no two emitted points can coincide
MAX_TURN = 1.4          # radians of turning one cubic is allowed to carry

# +1 unit of slack on the draw-on sweep so the reveal never trails a sliver of
# ink behind its own edge; much more and it visibly runs ahead of the letter.
MASK_SLACK = 1.0


# ── the spine, and the stroke around it ───────────────────────────────────


def bowl(t0, t1, n=SAMPLES):
    """Spine points, travel directions and half widths along one bowl.

    The bowl is centred at (0, -RY) so that the letter's centre — where this
    arc's rotation takes over — is the origin. Angles are in radians.
    """
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        yield ((RX * math.cos(t), -RY + RY * math.sin(t)),
               (RX * math.sin(t), -RY * math.cos(t)),
               HM + HS * math.cos(2 * t))


def edges(seg):
    """The two sides of the stroke: the spine pushed out by its half width."""
    a, b = [], []
    for (x, y), (dx, dy), h in seg:
        m = math.hypot(dx, dy)
        nx, ny = -dy / m * h, dx / m * h
        a.append((x + nx, y + ny))
        b.append((x - nx, y - ny))
    return a, b


def trim(pts, ycut):
    """Drop the leading points past the terminal and land exactly on the cut.

    The cut has to be dead horizontal, the way a grotesque cuts its terminals,
    so it is a clipping line rather than a cap struck square to the spine. The
    spine is about 3 degrees off vertical where it ends, and a square cap shows
    that tilt across the whole width of the stroke — roughly a unit of droop on
    a 17-unit cut, which reads as a mistake rather than as a style.
    """
    i = 0
    while i < len(pts) - 1 and pts[i][1] > ycut:
        i += 1
    if i:
        (x1, y1), (x2, y2) = pts[i - 1], pts[i]
        f = (ycut - y1) / (y2 - y1)
        return [(x1 + f * (x2 - x1), ycut)] + pts[i:]
    return pts


def rot(p):
    """A point turned 180 degrees about the letter's centre."""
    return (2 * CENTRE[0] - p[0], 2 * CENTRE[1] - p[1])


def turn(pts):
    """The other half of the letter: rotated 180 degrees, travelled backwards.

    Note which side comes back as which. Rotating reverses a point about the
    centre but leaves the direction of travel alone, and reversing negates the
    direction — the two cancel, so the left normal does not flip and the
    rotation of side A lands on side B. Swap them and the outline crosses
    itself.
    """
    return [rot(p) for p in reversed(pts)]


def sides():
    """Both edges of the whole letter, terminal to terminal."""
    top_a, top_b = edges(bowl(math.radians(T0), math.radians(-SWEEP)))
    ycut = -RY + CUT
    top_a, top_b = trim(top_a, ycut), trim(top_b, ycut)
    return top_a + turn(top_b)[1:], top_b + turn(top_a)[1:]


def spine(t0, n=SAMPLES):
    """The centreline from angle t0 round both bowls, as one open polyline."""
    half = [p for p, _, _ in bowl(t0, math.radians(-SWEEP), n)]
    return half + turn(half)[1:]


def nodes():
    """The five node centres: two measured, their rotations, and the join."""
    n = [(RX * math.cos(math.radians(t)), -RY + math.sin(math.radians(t)) * RY)
         for t in NODE_T]
    return n + [CENTRE] + [rot(p) for p in n]


def _cross(edge, c, r):
    """Where a polyline crosses a circle: (fractional index, point), in order."""
    out = []
    for i in range(len(edge) - 1):
        d0, d1 = math.dist(edge[i], c) - r, math.dist(edge[i + 1], c) - r
        if (d0 <= 0) != (d1 <= 0):
            f = d0 / (d0 - d1)
            out.append((i + f, (edge[i][0] + f * (edge[i + 1][0] - edge[i][0]),
                                edge[i][1] + f * (edge[i + 1][1] - edge[i][1]))))
    return out


def _walk(edge, u0, u1):
    """The piece of a polyline between two fractional indices, either way round."""
    def at(u):
        i = min(int(u), len(edge) - 2)
        f = u - i
        return (edge[i][0] + f * (edge[i + 1][0] - edge[i][0]),
                edge[i][1] + f * (edge[i + 1][1] - edge[i][1]))
    lo, hi = sorted((u0, u1))
    mid = [edge[i] for i in range(math.ceil(lo), math.floor(hi) + 1)]
    out = [at(lo)] + mid + [at(hi)]
    return out if u0 < u1 else out[::-1]


def _arc(c, p, q, clear, step=math.pi / 32, probes=15):
    """The arc of a circle from p to q that stays out of the channel.

    Two arcs join any two points on a circle, and the union's boundary is the
    one that runs round the OUTSIDE. Testing a single midpoint is not enough to
    tell them apart: where the channel runs through a node, the long way round
    passes over the far side of the disc, whose midpoint is a full radius clear
    of the channel and looks perfectly innocent. It is the quarter points, out
    at each end of the channel, that give it away — so probe the whole arc and
    take the one that is clear everywhere along it.
    """
    r = math.dist(c, p)
    a0 = math.atan2(p[1] - c[1], p[0] - c[0])
    a1 = math.atan2(q[1] - c[1], q[0] - c[0])
    on = lambda t: (c[0] + r * math.cos(a0 + t), c[1] + r * math.sin(a0 + t))
    d = (a1 - a0) % (2 * math.pi)
    for delta in (d, d - 2 * math.pi):
        if all(clear(on(delta * i / probes)) for i in range(1, probes)):
            break
    else:
        raise SystemExit("neither arc round a node stays out of the channel — "
                         "NODE_R and TRACE_W no longer describe a bead on a string")
    n = max(4, math.ceil(abs(delta) / step))
    return [on(delta * i / n) for i in range(n + 1)]


def circuit(n=2400):
    """The knockout: the exact boundary of the channel unioned with the nodes.

    The circuit has to come out as REAL GEOMETRY rather than as a stroke and
    five circles painted in the background colour, because the background is
    not always known — a transparent PNG has none, and a print vendor may be on
    any stock. An SVG <mask> would express it exactly and is what you reach for
    first, but Chrome rasterises masked content on its way into a PDF (checked:
    the page comes back as an /Image with an /SMask), which would quietly turn
    the whole print set into pictures of a logo.

    Overlapping subpaths cannot do it either. A channel plus five discs, all
    wound as holes, leaves the lens where a disc crosses the channel with a
    winding number of -1 and an even-odd depth of 3 — filled under both rules,
    so every node would come back with two ink pips in it.

    So the union is taken here, once, and what ships is its outline: a chain of
    beads on a string, traced up one side of the channel, round the far cap,
    and back down the other. Each node contributes an arc, each gap between
    nodes a piece of the channel's own edge, and they meet at genuine corners —
    which is why the pieces are kept separate all the way to the fitting.

    A swelling half width along the spine would have been three lines instead
    of forty, and is exact for a straight channel; this one bends, and it came
    out a fifth of a unit off — six per cent of a node's radius, which is a
    visibly oval node at print size.
    """
    pts = spine(math.radians(NODE_T[0]), n)
    T, w, C = tangents(pts), TRACE_W / 2, nodes()
    A = [(p[0] - t[1] * w, p[1] + t[0] * w) for p, t in zip(pts, T)]
    B = [(p[0] + t[1] * w, p[1] - t[0] * w) for p, t in zip(pts, T)]
    clear = lambda p: min(_dist_to_seg(p, pts[i], pts[i + 1])
                          for i in range(len(pts) - 1)) > w
    # Node order along the trace, which is not the order they are defined in:
    # the second bowl is traversed backwards, so its two nodes arrive swapped.
    order = sorted(range(len(C)),
                   key=lambda k: min(range(len(pts)),
                                     key=lambda i: math.dist(pts[i], C[k])))
    head, tail = C[order[0]], C[order[-1]]

    # The walk below assumes every node sits ON the channel, and that the two
    # outer ones are exactly where it starts and stops — otherwise a node
    # circle the channel never reaches returns no crossings and the whole thing
    # falls over several frames later with an IndexError about a list, which
    # tells a maintainer nothing about which number they moved.
    off = max(min(_dist_to_seg(c, pts[i], pts[i + 1])
                  for i in range(len(pts) - 1)) for c in C)
    if (math.dist(head, pts[0]) > 1e-6 or math.dist(tail, pts[-1]) > 1e-6
            or off > 1e-3):
        raise SystemExit("a node is off the channel — NODE_T has to name angles "
                         "the spine actually runs through, and its first angle "
                         "is where the channel starts")

    def run(edge, back):
        """One side of the channel, weaving over each bead on the way."""
        ends = _cross(edge, head if not back else tail, NODE_R)
        cur, out = (ends[-1] if back else ends[0])[0], []
        for k in (reversed(order[1:-1]) if back else order[1:-1]):
            xs = _cross(edge, C[k], NODE_R)
            enter, leave = (xs[1], xs[0]) if back else (xs[0], xs[1])
            out.append(_walk(edge, cur, enter[0]))
            out.append(_arc(C[k], enter[1], leave[1], clear))
            cur = leave[0]
        stop = _cross(edge, tail if not back else head, NODE_R)
        stop = (stop[0] if back else stop[-1])
        out.append(_walk(edge, cur, stop[0]))
        return out, out[0][0], stop[1]

    up, a_start, a_end = run(A, back=False)
    down, b_start, b_end = run(B, back=True)
    return (up + [_arc(tail, a_end, b_start, clear)]
            + down + [_arc(head, b_end, a_start, clear)])


# ── fitting and flattening ────────────────────────────────────────────────


def tangents(pts):
    """Unit direction of travel at every point of a densely sampled curve."""
    out = []
    for i in range(len(pts)):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        m = math.dist(a, b) or 1.0
        out.append(((b[0] - a[0]) / m, (b[1] - a[1]) / m))
    return out


def hermite(p0, t0, p1, t1):
    """One cubic from two points and the unit tangents there.

    The control arms are the length that reproduces a CIRCULAR arc exactly:
    (4/3)*tan(theta/4)*R, for the arc that shares those tangents. Catmull-Rom's
    sixth-of-a-chord arms are a small-angle approximation of the same thing and
    give up an order of accuracy for nothing.
    """
    ch = math.dist(p0, p1)
    th = math.acos(max(-1.0, min(1.0, t0[0] * t1[0] + t0[1] * t1[1])))
    d = ch / 3 if th < 1e-6 else (4 / 3) * math.tan(th / 4) * ch / (2 * math.sin(th / 2))
    d = max(0.0, min(d, ch))
    return ((p0[0] + t0[0] * d, p0[1] + t0[1] * d),
            (p1[0] - t1[0] * d, p1[1] - t1[1] * d), p1)


def _cubic_at(p0, seg, t):
    c1, c2, p3 = seg
    u = 1 - t
    return (u**3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t**3 * p3[1])


def _deviation(pts, i, j, seg):
    """Furthest the sampled curve strays from this cubic, both ways round."""
    n = max(8, 2 * (j - i))
    curve = [_cubic_at(pts[i], seg, k / n) for k in range(n + 1)]
    return max(max(min(_dist_to_seg(p, curve[k], curve[k + 1])
                       for k in range(len(curve) - 1)) for p in pts[i:j + 1]),
               max(min(_dist_to_seg(q, pts[k], pts[k + 1])
                       for k in range(i, j)) for q in curve))


def fit(pts, tol=None):
    """The curve as cubics, guaranteed within `tol` of the sampled geometry.

    Adaptive rather than a fixed knot count, because the deviation is not
    spread evenly: the letter is gentle for most of its length and then turns
    hard just before each terminal, where the inner edge of the stroke drops to
    a radius of about four units. Knots spaced by arc length put the same
    number of them either side of that and miss it by a quarter of a unit,
    which is a visible flat spot at print size; here the recursion just spends
    its segments where the curvature is.

    Each side of the letter is fitted on its own, and the two terminal cuts are
    then drawn as explicit straight lines. Fit the closed loop in one pass
    instead and the cuts get rounded off into a wobble, because nothing in the
    fit knows that a corner was meant to stay a corner.
    """
    tol = FIT_TOL if tol is None else tol
    T = tangents(pts)
    turn = [0.0]
    for a, b in zip(T, T[1:]):
        turn.append(turn[-1] + abs(math.atan2(a[0] * b[1] - a[1] * b[0],
                                              a[0] * b[0] + a[1] * b[1])))
    segs = []

    def rec(i, j, depth):
        # A cubic cannot carry much more than a quarter turn, and over a half
        # turn the two tangents stop telling it apart from its own reverse — so
        # split on the turning first and only then on how far off it is. Split
        # blindly to a fixed depth instead and every short arc round a node
        # comes back as eight segments doing the work of one.
        seg = hermite(pts[i], T[i], pts[j], T[j])
        if j - i > 2 and depth < 16 and (turn[j] - turn[i] > MAX_TURN
                                         or _deviation(pts, i, j, seg) > tol):
            m = (i + j) // 2
            rec(i, m, depth + 1)
            rec(m, j, depth + 1)
        else:
            segs.append(seg)

    rec(0, len(pts) - 1, 0)
    return pts[0], segs


def flatten(start, segs, tol):
    """The fitted cubics as a polyline within `tol` of the curve.

    Subdivision count from the standard bound: a cubic split into n pieces is
    within max|B''| / (8 n^2) of its chords. The PNG builders get this rather
    than the ideal geometry, so the raster and the vector are flattenings of
    the SAME curve and cannot disagree by more than the tolerance.
    """
    pts = [start]
    for c1, c2, p3 in segs:
        p0 = pts[-1]
        b2 = 6 * max(math.hypot(p0[0] - 2 * c1[0] + c2[0],
                                p0[1] - 2 * c1[1] + c2[1]),
                     math.hypot(c1[0] - 2 * c2[0] + p3[0],
                                c1[1] - 2 * c2[1] + p3[1]))
        n = max(1, math.ceil(math.sqrt(b2 / (8 * tol)))) if b2 > 0 else 1
        for k in range(1, n + 1):
            t, u = k / n, 1 - k / n
            pts.append((u**3 * p0[0] + 3 * u * u * t * c1[0]
                        + 3 * u * t * t * c2[0] + t**3 * p3[0],
                        u**3 * p0[1] + 3 * u * u * t * c1[1]
                        + 3 * u * t * t * c2[1] + t**3 * p3[1]))
    return pts


def dedupe(poly, eps=POLY_EPS, closed=False):
    """Drop points too close to their neighbour to survive being written out.

    The pieces of each outline are fitted separately and meet end to end, so
    every join contributes a duplicate — and the two copies differ only in the
    last few bits, which then round to the same pair of decimals. That leaves a
    zero-length segment in the emitted polygon: harmless to fill, but it makes
    the outline look self-intersecting to anything that goes looking, and it is
    cheaper not to emit it than to explain it.
    """
    out = []
    for p in poly:
        if not out or math.dist(p, out[-1]) > eps:
            out.append(p)
    if closed and len(out) > 1 and math.dist(out[0], out[-1]) <= eps:
        out.pop()
    return out


# ── measurement ───────────────────────────────────────────────────────────


def _dist_to_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-18 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - dx * t, p[1] - a[1] - dy * t)


def _spans(poly, y):
    """The x-intervals where the horizontal line at y is inside the outline."""
    xs = []
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y):
            xs.append(x1 + (x2 - x1) * (y - y1) / (y2 - y1))
    xs.sort()
    return list(zip(xs[0::2], xs[1::2]))


def union_error(ribbon, trace, centres, scale):
    """How far the ribbon sits from the union it stands in for.

    The ribbon's swelling half width is the union of channel and node discs
    exactly when the spine is straight, and this letter's is not. So check it
    rather than trust it: on the true boundary the signed distance

        min(dist to channel - TRACE_W/2, min over nodes of |p - c| - NODE_R)

    is zero, and the largest departure from zero along the ribbon is the error,
    in output units.
    """
    worst = 0.0
    for p in ribbon:
        d = min(_dist_to_seg(p, trace[i], trace[i + 1])
                for i in range(len(trace) - 1)) - TRACE_W * scale / 2
        for c in centres:
            d = min(d, math.dist(p, c) - NODE_R * scale)
        worst = max(worst, abs(d))
    return worst


def mask_width(poly, skel, step=0.1):
    """How wide the sweep has to be to cover every part of the letter.

    Here this is known in advance — every ink point is within h(t) of its own
    spine point by construction, and the terminal trim only ever removes
    material, so the answer is 2*(HM+HS) scaled. That is worth having anyway,
    because it is exactly the measurement that went wrong on the mark this one
    replaces: distance to a polyline is a min of convex functions, so it is
    neither convex, nor maximised at a vertex, nor maximised on the boundary,
    and a boundary-only sweep quietly under-reported.

    So this walks the outline AND the interior on a grid, and the build fails
    if it disagrees with the analytic value. Distance to a set is 1-Lipschitz,
    so the true maximum cannot exceed the sampled one by more than the grid's
    half-diagonal, which is added below.
    """
    def d(p):
        return min(_dist_to_seg(p, skel[k], skel[k + 1])
                   for k in range(len(skel) - 1))

    worst = 0.0
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        n = max(1, math.ceil(math.dist(a, b) / step))
        for j in range(n + 1):
            f = j / n
            worst = max(worst, d((a[0] + (b[0] - a[0]) * f,
                                  a[1] + (b[1] - a[1]) * f)))

    ys = [p[1] for p in poly]
    y = min(ys) + step / 2
    while y < max(ys):
        for x0, x1 in _spans(poly, y):
            n = max(1, math.ceil((x1 - x0) / step))
            for j in range(n + 1):
                worst = max(worst, d((x0 + (x1 - x0) * j / n, y)))
        y += step
    return 2 * (worst + step * math.sqrt(0.5))


# ── emit ──────────────────────────────────────────────────────────────────


def path_d(start, segs, move="M", prec=3):
    """The fitted cubics as SVG. `move` opens the run — "M" to start a path,
    "L" to draw the straight terminal cut into it, None to carry straight on
    from wherever the pen already is."""
    f = "%." + str(prec) + "f"
    out = [] if move is None else [(move + f + " " + f) % start]
    for c1, c2, p3 in segs:
        out.append(("C" + " ".join([f] * 6)) % (c1 + c2 + p3))
    return " ".join(out)


def chain(pieces):
    """Fit a list of end-to-end pieces into one continuous run of cubics.

    Each piece is fitted alone so the corner between them survives; only the
    first gets a move, because every piece after it starts exactly where the
    last one finished.
    """
    d, poly = [], []
    for i, pc in enumerate(pieces):
        st, segs = fit(pc)
        d.append(path_d(st, segs, move="M" if i == 0 else None))
        poly += flatten(st, segs, FLATTEN_TOL)
    return " ".join(d), poly


def circle_d(cx, cy, r, prec=3):
    """A circle as its own subpath — two half-arcs, so it closes cleanly."""
    f = "%." + str(prec) + "f"
    return (("M" + f + " " + f + " A" + f + " " + f + " 0 1 0 " + f + " " + f
             + " A" + f + " " + f + " 0 1 0 " + f + " " + f + " Z")
            % (cx + r, cy, r, r, cx - r, cy, r, r, cx + r, cy))


def wrap(text, f, width=86):
    for i in range(0, len(text), width):
        f.write(f'    "{text[i:i + width]}"\n')


def poly_block(poly, f, per_line=5):
    for i in range(0, len(poly), per_line):
        f.write("    " + " ".join("(%.2f, %.2f)," % p for p in poly[i:i + per_line]) + "\n")


# ── build ─────────────────────────────────────────────────────────────────


def main():
    a, b = sides()
    xs = [p[0] for p in a + b]
    ys = [p[1] for p in a + b]
    x0, y0 = min(xs), min(ys)
    s = BOX_H / (max(ys) - y0)
    box_w = (max(xs) - x0) * s
    put = lambda pts: [((x - x0) * s, (y - y0) * s) for x, y in pts]

    # The outline: each side fitted on its own, joined by two straight cuts.
    sa, ca = fit(put(a))
    sb, cb = fit(put(b)[::-1])
    mark_path = path_d(sa, ca) + " " + path_d(sb, cb, move="L") + " Z"
    poly = dedupe(flatten(sa, ca, FLATTEN_TOL) + flatten(sb, cb, FLATTEN_TOL),
                  closed=True)

    slip = max(abs(min(p[0] for p in poly)), abs(min(p[1] for p in poly)),
               abs(max(p[0] for p in poly) - box_w),
               abs(max(p[1] for p in poly) - BOX_H))
    if slip > 0.02:
        raise SystemExit(f"ink is not tight to its box (off by {slip:.4f}) — "
                         "the flattening tolerance and the box no longer agree")

    # The circuit: one closed ribbon up one side of the channel, round the far
    # node, and back down the other. Every piece is fitted on its own so the
    # corners where a node's disc crosses the channel stay corners.
    ribbon_d, ribbon_poly = chain([put(pc) for pc in circuit()])
    ribbon_poly = dedupe(ribbon_poly, closed=True)

    node_pts = put(nodes())
    hole_r = HOLE_R * s
    circuit_path = ribbon_d + " Z " + " ".join(
        circle_d(x, y, hole_r) for x, y in node_pts)
    slack = union_error(ribbon_poly, put(spine(math.radians(NODE_T[0]))),
                        node_pts, s)
    # What is left here is the fit's own tolerance, so the trip wire is set to
    # catch a structural mistake rather than noise: pick the wrong arc round a
    # node and this reads about 1.7, a whole channel width.
    if slack > FIT_TOL + FLATTEN_TOL + 0.02:
        raise SystemExit(f"the ribbon is {slack:.3f} units off the true union of "
                         "channel and nodes — the boundary walk has lost the plot")

    # The draw-on skeleton: the same spine again, but started where the
    # terminal is actually cut, so a round cap of MASK_W/2 lands exactly on the
    # cut instead of hanging past it and popping the terminal in early.
    t_cut = math.asin(CUT / RY)
    sk, ck = fit(put(spine(t_cut)))
    skel_d = path_d(sk, ck)
    skel_poly = dedupe(flatten(sk, ck, FLATTEN_TOL))

    analytic = 2 * (HM + HS) * s
    measured = mask_width(poly, skel_poly)
    if measured > analytic + 2 * MASK_SLACK:
        raise SystemExit(f"sweep measured {measured:.2f} but the geometry says "
                         f"{analytic:.2f} — the skeleton no longer follows the spine")
    # The analytic value is exact for the true spine; the skeleton shipped is a
    # 30-knot fit of it, so take whichever is larger.
    mask_w = round(max(analytic, measured) + MASK_SLACK, 2)

    with open(OUT, "w") as f:
        f.write(f'''"""GENERATED by tools/design_mark.py — do not edit by hand.

The Southern AI Consulting S: a stroked ellipse and its own 180-degree
rotation, in a {box_w:.2f} x {BOX_H:.0f} box, ink tight to the box on all four sides (no
padding is baked in). One closed outline, no corners in it except the two
terminal cuts, and a circuit trace that IS the letter's own centreline.

MARK_PATH     the letterform alone: one closed subpath of cubics, no overlaps
              and no fill-rule subtlety. This IS the reduction — below
              {SOLID_BELOW_PX} px of ink, ship this and nothing else.
CIRCUIT_PATH  the knockout: one closed ribbon down the letter's own centreline
              that swells to a disc at each of the five nodes, plus the five
              ink dots as islands inside it. Append it to MARK_PATH in ONE
              path element with fill-rule="evenodd" and fill the result in a
              single colour — see below.
MARK_POLY     the letter outline flattened to {len(poly)} points, and
RIBBON_POLY   the ribbon flattened to {len(ribbon_poly)}, for the Pillow builders, which
              cannot draw a curve. Both within {FLATTEN_TOL} units. Pillow has no
              even-odd fill either, so it paints the letter, knocks the ribbon
              back out, and puts NODES/HOLE_R dots on top — same region.
SKELETON_D    the centreline again, for the draw-on mask in styles.css.
MASK_W        stroke width that fully covers the letter when swept along it.

The circuit is a KNOCKOUT, not a second ink: it is a hole, and whatever the
mark is sitting on shows through it. So the artwork is one colour everywhere,
a one-plate job loses nothing, it needs no background colour passed in, and on
the site it follows the light/dark theme without being told. Below
{SOLID_BELOW_PX} px of ink the channel closes up; the letter on its own holds to 7 px.
"""

MARK_W = {box_w:.2f}
MARK_H = {BOX_H:.1f}

MARK_PATH = (
''')
        wrap(mark_path, f)
        f.write(")\n\nCIRCUIT_PATH = (\n")
        wrap(circuit_path, f)
        f.write(")\n\nMARK_POLY = (\n")
        poly_block(poly, f)
        f.write(")\n\nRIBBON_POLY = (\n")
        poly_block(ribbon_poly, f)
        f.write(")\n\nNODES = (\n")
        poly_block(node_pts, f)
        f.write(f")\n\nHOLE_R = {hole_r:.2f}\n")
        f.write(f"TRACE_W = {TRACE_W * s:.2f}   # channel width, for reference\n")
        f.write(f"NODE_R = {NODE_R * s:.2f}    # node disc radius, for reference\n")
        f.write("\nSKELETON_D = (\n")
        wrap(skel_d, f)
        f.write(f')\n\nMASK_W = {mask_w}\n\n'
                f'# Below this much ink height, ship MARK_PATH on its own.\n'
                f'SOLID_BELOW_PX = {SOLID_BELOW_PX}\n')

    print(f"  {OUT}")
    print(f"  box {box_w:.2f} x {BOX_H:.0f} (aspect {box_w / BOX_H:.4f}), "
          f"{len(poly)} + {len(ribbon_poly)} flattened points")
    print(f"  stroke {2 * (HM - HS) * s:.2f}-{analytic:.2f} units, "
          f"channel {TRACE_W * s:.2f}, nodes {NODE_R * s:.2f}/{hole_r:.2f}")
    print(f"  mask stroke {mask_w} (analytic {analytic:.2f}, "
          f"measured {measured:.2f})")
    print(f"  ribbon is within {slack:.4f} units of the true channel/node union")


if __name__ == "__main__":
    main()
