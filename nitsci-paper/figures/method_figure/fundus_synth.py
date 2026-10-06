"""Synthetic fundus photographs and derived maps for the method figure.

The figure uses synthetic images so it can be built without the datasets.
To use real IDRiD images instead, pass their paths to make_method_figure.py
(--fundus a.jpg b.jpg ...); everything derived from them (Ben Graham view,
augmentations) is then computed from the real photographs.
"""
import cv2
import numpy as np

S = 512


def _mask(size=S, r=0.47):
    yy, xx = np.mgrid[:size, :size]
    return ((xx - size / 2) ** 2 + (yy - size / 2) ** 2) <= (r * size) ** 2


def _arc(p0, p1, bend, n=40):
    """Quadratic Bezier from p0 to p1 bending sideways by `bend` (fraction of length)."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    c = (p0 + p1) / 2 + bend * np.array([-d[1], d[0]])
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 2) * p0 + 2 * (1 - t) * t * c + t ** 2 * p1


def fundus(seed=0, grade=3, size=S):
    """Return (rgb uint8 image, dict of lesion masks EX/SE/HE/MA)."""
    rng = np.random.RandomState(seed)
    yy, xx = np.mgrid[:size, :size] / size
    r = np.sqrt((xx - 0.5) ** 2 + (yy - 0.5) ** 2) / 0.47
    od = np.array([0.70 + rng.uniform(-0.02, 0.02), 0.47 + rng.uniform(-0.03, 0.03)])
    mac = np.array([0.40, 0.50])

    # background: warm orange-red with vignetting and choroidal texture
    base = np.stack([0.86 - 0.38 * r ** 2, 0.42 - 0.27 * r ** 2, 0.17 - 0.12 * r ** 2], -1)
    tex = cv2.GaussianBlur(rng.rand(size, size).astype(np.float32), (0, 0), 6)
    tex = (tex - tex.mean()) / (tex.std() + 1e-6)
    base += 0.025 * tex[..., None] * np.array([1.0, 0.6, 0.3])
    dmac = np.sqrt((xx - mac[0]) ** 2 + (yy - mac[1]) ** 2)
    base *= (1 - 0.28 * np.exp(-(dmac / 0.09) ** 2))[..., None]
    dod = np.sqrt((xx - od[0]) ** 2 + (yy - od[1]) ** 2)
    glow = np.exp(-(dod / 0.055) ** 2)
    base = base * (1 - glow[..., None]) + glow[..., None] * np.array([1.0, 0.86, 0.55])
    img = np.clip(base, 0, 1)

    # vessels: superior/inferior temporal arcades curving around the macula, short nasal vessels
    ves = np.zeros((size, size), np.float32)

    def cubic(p0, c1, c2, p1, n=60):
        t = np.linspace(0, 1, n)[:, None]
        p0, c1, c2, p1 = (np.array(v, float) * size for v in (p0, c1, c2, p1))
        return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * p1

    def draw(pts, w0, w1):
        for i in range(len(pts) - 1):
            w = int(round(w0 + (w1 - w0) * i / len(pts)))
            cv2.line(ves, tuple(pts[i].astype(int)), tuple(pts[i + 1].astype(int)), 1.0, max(1, w), cv2.LINE_AA)

    trunks = []
    for sgn in (-1, 1):
        j = rng.uniform(-0.02, 0.02, 4)
        trunks.append((cubic(od, (od[0] - 0.05, 0.5 + sgn * 0.22 + j[0]), (0.42 + j[1], 0.5 + sgn * 0.36),
                             (0.12 + j[2], 0.5 + sgn * 0.26 + j[3])), 7, 3))
        trunks.append((cubic(od, (od[0] - 0.08, 0.5 + sgn * 0.08), (0.48, 0.5 + sgn * 0.17),
                             (0.30, 0.5 + sgn * 0.12)), 4, 2))
        trunks.append((cubic(od, (od[0] + 0.06, 0.5 + sgn * 0.12), (0.88, 0.5 + sgn * 0.25),
                             (0.92, 0.5 + sgn * 0.33)), 5, 2))
    for pts, w0, w1 in trunks:
        draw(pts, w0, w1)
        for _ in range(3):
            i = rng.randint(15, len(pts) - 8)
            d = pts[i + 1] - pts[i]
            nrm = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
            side = rng.choice([-1, 1])
            end = pts[i] + side * nrm * rng.uniform(35, 70) + d * rng.uniform(4, 10)
            mid = (pts[i] + end) / 2 + side * nrm * 8
            br = np.array([pts[i] + (mid - pts[i]) * t for t in np.linspace(0, 1, 8)] +
                          [mid + (end - mid) * t for t in np.linspace(0, 1, 8)])
            draw(br, max(1, w1), 1)
    ves = cv2.GaussianBlur(ves, (0, 0), 1.0)
    vcol = np.array([0.50, 0.07, 0.04])
    img = img * (1 - 0.85 * ves[..., None]) + 0.85 * ves[..., None] * vcol

    # lesions, more with higher grade
    masks = {k: np.zeros((size, size), np.float32) for k in ('EX', 'SE', 'HE', 'MA')}
    n = {'MA': 4 + 4 * grade, 'HE': 2 * grade, 'EX': 3 * grade, 'SE': max(0, grade - 1)}

    def spot(cx, cy, rad, key, color, soft=1.0):
        m = np.zeros((size, size), np.float32)
        cv2.circle(m, (int(cx), int(cy)), max(1, int(rad)), 1.0, -1, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), soft)
        masks[key] = np.maximum(masks[key], (m > 0.3).astype(np.float32))
        return m, color

    layers = []
    for _ in range(n['MA']):
        a, d = rng.uniform(0, 2 * np.pi), rng.uniform(0.05, 0.33)
        layers.append(spot(size * (mac[0] + d * np.cos(a)), size * (mac[1] + d * np.sin(a)),
                           rng.uniform(2, 3.5), 'MA', np.array([0.45, 0.02, 0.02]), 0.8))
    for _ in range(n['HE']):
        a, d = rng.uniform(0, 2 * np.pi), rng.uniform(0.08, 0.36)
        layers.append(spot(size * (mac[0] + d * np.cos(a)), size * (mac[1] + d * np.sin(a)),
                           rng.uniform(6, 13), 'HE', np.array([0.40, 0.02, 0.02]), 2.5))
    for _ in range(n['EX']):
        a, d = rng.uniform(0, 2 * np.pi), rng.uniform(0.06, 0.22)
        cx, cy = size * (mac[0] + d * np.cos(a)), size * (mac[1] + d * np.sin(a))
        for _ in range(rng.randint(2, 6)):
            layers.append(spot(cx + rng.uniform(-14, 14), cy + rng.uniform(-14, 14), rng.uniform(2.5, 5.5),
                               'EX', np.array([1.0, 0.93, 0.45]), 0.9))
    for _ in range(n['SE']):
        a, d = rng.uniform(0, 2 * np.pi), rng.uniform(0.12, 0.3)
        layers.append(spot(size * (od[0] - 0.15 + d * 0.4 * np.cos(a)), size * (od[1] + d * np.sin(a)),
                           rng.uniform(10, 16), 'SE', np.array([0.97, 0.90, 0.80]), 6))
    for m, col in layers:
        a = np.clip(m, 0, 1)[..., None] * 0.9
        img = img * (1 - a) + a * col

    img = cv2.GaussianBlur(img.astype(np.float32), (0, 0), 0.7)
    img[~_mask(size)] = 0
    return (np.clip(img, 0, 1) * 255).astype(np.uint8), masks


def ben_graham(img, size=S):
    out = cv2.addWeighted(img, 4, cv2.GaussianBlur(img, (0, 0), size / 30), -4, 128)
    m = _mask(size, 0.46)
    out[~m] = 128
    return out


def lesion_map_rgb(masks, size=S):
    """Black background, colour-coded lesions (EX yellow, SE white, HE green, MA red), as in lesion figures."""
    out = np.zeros((size, size, 3), np.float32)
    for k, c in (('HE', (0.1, 0.85, 0.1)), ('EX', (1, 0.95, 0.1)), ('SE', (0.9, 0.9, 0.9)), ('MA', (1, 0.1, 0.1))):
        m = cv2.dilate(masks[k], np.ones((3, 3), np.uint8)) if k == 'MA' else masks[k]
        out[m > 0] = c
    return (out * 255).astype(np.uint8)


def attention_map(masks, size=S, seed=0):
    """Smooth lesion-attention map m in [0, 1], high around lesions (what the lesion head should learn)."""
    rng = np.random.RandomState(seed)
    acc = sum(masks[k] * w for k, w in (('HE', 1.0), ('EX', 0.9), ('MA', 1.0), ('SE', 0.7)))
    acc = cv2.GaussianBlur(acc.astype(np.float32), (0, 0), 14)
    acc += 0.08 * cv2.GaussianBlur(rng.rand(size, size).astype(np.float32), (0, 0), 30)
    acc = acc / (acc.max() + 1e-6)
    acc[~_mask(size)] = 0
    return acc


def overlay(img, att, alpha=0.55):
    import matplotlib.cm as cm
    heat = (cm.jet(att)[..., :3] * 255).astype(np.float32)
    out = img.astype(np.float32) * (1 - alpha * att[..., None]) + heat * alpha * att[..., None]
    out[~_mask(img.shape[0])] = 0
    return np.clip(out, 0, 255).astype(np.uint8)


def feature_maps(img, n=6, size=64, seed=0):
    """Pseudo feature maps: filtered, down-sampled versions of the image."""
    rng = np.random.RandomState(seed)
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    g = cv2.resize(g, (size * 2, size * 2), interpolation=cv2.INTER_AREA)
    maps = []
    for i in range(n):
        k = rng.randn(5, 5).astype(np.float32)
        f = cv2.filter2D(g, -1, k)
        f = cv2.resize(np.abs(f), (size, size), interpolation=cv2.INTER_AREA)
        maps.append((f - f.min()) / (f.ptp() + 1e-6) if hasattr(f, 'ptp') else (f - f.min()) / (np.ptp(f) + 1e-6))
    return maps
