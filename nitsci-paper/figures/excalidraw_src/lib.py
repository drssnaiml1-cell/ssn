"""Tiny helpers for hand-placed Excalidraw elements (fontFamily 2 = Helvetica)."""
import itertools, json

_seed = itertools.count(1000)
ELEMS = []

# palette (skill color-palette.md)
NAVY = '#1e3a5f'; BLUE = '#3b82f6'; BLUE2 = '#60a5fa'; BLUE3 = '#93c5fd'; BLUE4 = '#dbeafe'
ORANGE_F = '#fed7aa'; ORANGE_S = '#c2410c'
GREEN_F = '#a7f3d0'; GREEN_S = '#047857'
RED_F = '#fee2e2'; RED_S = '#dc2626'
YEL_F = '#fef3c7'; YEL_S = '#b45309'
PUR_F = '#ddd6fe'; PUR_S = '#6d28d9'
TITLE = '#1e40af'; SUB = '#3b82f6'; BODY = '#64748b'; ONLIGHT = '#374151'
FUNDUS = '#e8853a'; FUNDUS_S = '#9a3412'


def _base(t, x, y, w, h, stroke=NAVY, fill='transparent', sw=2, style='solid', **kw):
    s = next(_seed)
    e = dict(type=t, id=kw.pop('id', f'{t}{s}'), x=x, y=y, width=w, height=h, angle=0,
             strokeColor=stroke, backgroundColor=fill, fillStyle='solid', strokeWidth=sw,
             strokeStyle=style, roughness=0, opacity=100, groupIds=[], seed=s, version=1,
             versionNonce=s + 7, isDeleted=False, boundElements=None, link=None, locked=False,
             strokeSharpness='sharp')
    e.update(kw)
    ELEMS.append(e)
    return e


def rect(x, y, w, h, fill='transparent', stroke=NAVY, sw=2, style='solid', round_=True):
    e = _base('rectangle', x, y, w, h, stroke, fill, sw, style)
    if round_:
        e['strokeSharpness'] = 'round'; e['roundness'] = {'type': 3}
    return e


def ellipse(x, y, w, h, fill='transparent', stroke=NAVY, sw=2, style='solid'):
    return _base('ellipse', x, y, w, h, stroke, fill, sw, style)


def diamond(x, y, w, h, fill='transparent', stroke=NAVY, sw=2):
    return _base('diamond', x, y, w, h, stroke, fill, sw)


def text(x, y, s, size=18, color=ONLIGHT, align='left', w=None, bold=False):
    lines = s.split('\n')
    lh = 1.25
    width = w if w is not None else max(len(l) for l in lines) * size * 0.55
    h = len(lines) * size * lh
    return _base('text', x, y, width, h, color, 'transparent', 1, 'solid', text=s, originalText=s,
                 fontSize=size, fontFamily=2, textAlign=align, verticalAlign='top',
                 baseline=round(size * 0.9 + (len(lines) - 1) * size * lh), lineHeight=lh,
                 containerId=None)


def label(box, s, size=18, color=ONLIGHT, dy=0):
    """Text centred in a box."""
    n = len(s.split('\n'))
    h = n * size * 1.25
    return text(box['x'], box['y'] + (box['height'] - h) / 2 + dy, s, size, color, 'center', w=box['width'])


def box(x, y, w, h, s, fill, stroke, size=18, color=ONLIGHT, style='solid', sw=2):
    b = rect(x, y, w, h, fill, stroke, sw, style)
    label(b, s, size, color)
    return b


def arrow(pts, color=NAVY, sw=2, style='solid', head='arrow', start=None):
    x0, y0 = pts[0]
    rel = [[px - x0, py - y0] for px, py in pts]
    xs = [p[0] for p in rel]; ys = [p[1] for p in rel]
    return _base('arrow', x0, y0, max(xs) - min(xs), max(ys) - min(ys), color, 'transparent', sw, style,
                 points=rel, startArrowhead=start, endArrowhead=head, lastCommittedPoint=None,
                 startBinding=None, endBinding=None)


def line(pts, color=NAVY, sw=2, style='solid'):
    x0, y0 = pts[0]
    rel = [[px - x0, py - y0] for px, py in pts]
    xs = [p[0] for p in rel]; ys = [p[1] for p in rel]
    return _base('line', x0, y0, max(xs) - min(xs), max(ys) - min(ys), color, 'transparent', sw, style,
                 points=rel, lastCommittedPoint=None, startBinding=None, endBinding=None,
                 startArrowhead=None, endArrowhead=None)


def fundus(cx, cy, r, lesions=True):
    """Stylised fundus photograph: orange disc, optic disc, a few vessels and lesions."""
    ellipse(cx - r, cy - r, 2 * r, 2 * r, FUNDUS, FUNDUS_S, 2)
    ellipse(cx + r * 0.35, cy - r * 0.18, r * 0.32, r * 0.32, '#fde68a', '#f59e0b', 1)
    od = (cx + r * 0.51, cy - r * 0.02)
    for dx, dy in [(-0.8, -0.45), (-0.85, 0.4), (-0.3, -0.85), (-0.25, 0.85)]:
        line([od, (cx + r * dx * 0.55, cy + r * dy * 0.55), (cx + r * dx * 0.9, cy + r * dy * 0.9)], '#b91c1c', 1)
    if lesions:
        for dx, dy, c, s in [(-0.3, -0.2, '#7f1d1d', 0.07), (-0.45, 0.25, '#7f1d1d', 0.05),
                             (0.0, 0.35, '#fef08a', 0.09), (-0.1, -0.45, '#fef08a', 0.06), (-0.55, -0.05, '#7f1d1d', 0.04)]:
            ellipse(cx + r * dx, cy + r * dy, r * s * 2, r * s * 2, c, c, 1)


def grid(x, y, n, cell, hot=(), fill=BLUE4, hotfill=ORANGE_S, stroke=NAVY, warm=()):
    for i in range(n):
        for j in range(n):
            f = hotfill if (i, j) in hot else ('#fdba74' if (i, j) in warm else fill)
            rect(x + j * cell, y + i * cell, cell, cell, f, stroke, 1, round_=False)


def save(path):
    doc = dict(type='excalidraw', version=2, source='https://excalidraw.com', elements=ELEMS,
               appState=dict(viewBackgroundColor='#ffffff', gridSize=20), files={})
    with open(path, 'w') as f:
        json.dump(doc, f, indent=1)
    print(len(ELEMS), 'elements ->', path)
