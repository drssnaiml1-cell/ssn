"""Method overview figure for the NITSCI paper (HEL-Net-style, matplotlib).

    python make_method_figure.py                 # synthetic fundus images
    python make_method_figure.py --fundus a.jpg b.jpg c.jpg   # real IDRiD/APTOS photographs

Writes ../nitsci_method.pdf (vector, for LaTeX) and ../nitsci_method.png (600 dpi).
"""
import argparse
import os

import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib.patches import FancyArrow, FancyBboxPatch, Polygon, Rectangle
from matplotlib.transforms import Affine2D

import fundus_synth as fs

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Liberation Serif', 'Times New Roman', 'DejaVu Serif'],
                     'mathtext.fontset': 'stix', 'font.size': 11})

# colours (HEL-Net-like palette)
PANEL_A, PANEL_A_E = '#dde8f6', '#7f9fcf'
PANEL_B_E = '#4f9a4f'
SUB1, SUB1_E = '#e9f5e3', '#6aa86a'
SUB2, SUB2_E = '#f0f0f0', '#9a9a9a'
ORANGE, ORANGE_E = '#f08a3c', '#b85b17'
PINK, PINK_E = '#f9c9cf', '#e48a96'
BLUE, BLUE_E = '#4a7fd4', '#23488f'
LBLUE = '#cfe0f7'
GREEN_ARROW = '#7cc36b'
NAVY = '#1f3a68'
PURPLE, PURPLE_E = '#d9cdf2', '#6b4fb3'
RED = '#c62828'

fig = plt.figure(figsize=(12, 11.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100); ax.set_ylim(0, 95); ax.set_aspect('equal'); ax.axis('off')


# ---------------------------------------------------------------- helpers
def rbox(x, y, w, h, fc, ec, lw=1.2, ls='-', r=1.2, z=1, alpha=1):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={r}', fc=fc, ec=ec, lw=lw, ls=ls,
                       zorder=z, alpha=alpha)
    ax.add_patch(p)
    return p


def txt(x, y, s, size=11, bold=True, ha='center', va='center', color='black', style='normal', z=20, rot=0):
    ax.text(x, y, s, fontsize=size, fontweight='bold' if bold else 'normal', ha=ha, va=va, color=color,
            style=style, zorder=z, rotation=rot)


def image(a, x, y, w, h, z=5, border='white', lw=0.6):
    ax.imshow(a, extent=[x, x + w, y, y + h], zorder=z, interpolation='bilinear')
    if border:
        ax.add_patch(Rectangle((x, y), w, h, fill=False, ec=border, lw=lw, zorder=z + 0.1))


def stack(imgs, x, y, w, h, dx=0.9, dy=0.9, border='white'):
    for k, a in enumerate(imgs[::-1]):
        j = len(imgs) - 1 - k
        image(a, x + j * dx, y + j * dy, w, h, z=5 + k, border=border)


def skew_image(a, x, y, w, h, z=5, skew=25, edge='#555555'):
    """Image drawn as a parallelogram (perspective-like feature-map slice)."""
    tr = Affine2D().scale(w / a.shape[1], h / a.shape[0]).skew_deg(0, skew).translate(x, y) + ax.transData
    im = ax.imshow(a[::-1], extent=None, zorder=z, cmap='viridis', interpolation='bilinear')
    im.set_transform(tr)
    k = np.tan(np.radians(skew)) * w
    ax.add_patch(Polygon([(x, y), (x + w, y + k), (x + w, y + k + h), (x, y + h)], closed=True, fill=False,
                         ec=edge, lw=0.6, zorder=z + 0.1))


def arrow(x1, y1, x2, y2, color=NAVY, lw=1.4, ls='-', head=7, z=15, conn='arc3'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), zorder=z,
                arrowprops=dict(arrowstyle=f'-|>,head_length={head / 10},head_width={head / 20}', color=color, lw=lw,
                                ls=ls, shrinkA=0, shrinkB=0, connectionstyle=conn))


def path_arrow(pts, color=NAVY, lw=1.4, ls='-', z=15):
    xs, ys = zip(*pts)
    ax.plot(xs[:-1] + (xs[-1],), ys[:-1] + (ys[-1],), color=color, lw=lw, ls=ls, zorder=z, solid_capstyle='butt')
    arrow(xs[-2], ys[-2], xs[-1], ys[-1], color, lw, ls, z=z)


def fat(x1, y1, x2, y2, color=GREEN_ARROW, width=0.9, z=12):
    dx, dy = x2 - x1, y2 - y1
    ax.add_patch(FancyArrow(x1, y1, dx, dy, width=width, head_width=width * 2.1, head_length=1.1,
                            length_includes_head=True, fc=color, ec='none', zorder=z))


def cuboid(x, y, w, h, d, fc, ec=BLUE_E, z=6):
    """3-D block: front face + top + side, depth d drawn up-right."""
    c = np.array(matplotlib.colors.to_rgb(fc))
    ax.add_patch(Rectangle((x, y), w, h, fc=c, ec=ec, lw=0.7, zorder=z))
    ax.add_patch(Polygon([(x, y + h), (x + d, y + h + d * 0.6), (x + w + d, y + h + d * 0.6), (x + w, y + h)],
                         fc=np.clip(c * 1.25, 0, 1), ec=ec, lw=0.7, zorder=z))
    ax.add_patch(Polygon([(x + w, y), (x + w + d, y + d * 0.6), (x + w + d, y + h + d * 0.6), (x + w, y + h)],
                         fc=c * 0.75, ec=ec, lw=0.7, zorder=z))


def token_grid(x, y, size, n, colors, z=6, ec='#555555'):
    c = size / n
    for i in range(n):
        for j in range(n):
            ax.add_patch(Rectangle((x + j * c, y + (n - 1 - i) * c), c, c, fc=colors[i, j], ec=ec, lw=0.25, zorder=z))


def vector(x, y, n, c, cell=0.9, z=6, label=None):
    for i in range(n):
        ax.add_patch(Rectangle((x, y + i * cell), cell, cell, fc=c, ec='#444444', lw=0.4, zorder=z))
    if label:
        txt(x + cell / 2, y - 1.1, label, 11, True)


def title_tab(x, y, s, w, fc='white', ec=PANEL_A_E):
    rbox(x - w / 2, y - 1.3, w, 2.6, fc, ec, 1.0, r=0.6, z=8)
    txt(x, y, s, 13, True, z=9)


# ---------------------------------------------------------------- images
ap = argparse.ArgumentParser()
ap.add_argument('--fundus', nargs='*', default=None, help='real fundus photographs (at least 3)')
args = ap.parse_args()
if args.fundus:
    def load(p):
        im = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB)
        g = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY); ys, xs = np.where(g > 10)
        im = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; s = max(im.shape[:2])
        sq = np.zeros((s, s, 3), np.uint8); h, w = im.shape[:2]
        sq[(s - h) // 2:(s - h) // 2 + h, (s - w) // 2:(s - w) // 2 + w] = im
        return cv2.resize(sq, (fs.S, fs.S), interpolation=cv2.INTER_AREA)
    F = [load(p) for p in args.fundus]
    _, MASKS = fs.fundus(1, 3)
else:
    F = [fs.fundus(s, g)[0] for s, g in [(1, 3), (2, 1), (5, 4), (7, 2), (9, 0), (11, 3)]]
    _, MASKS = fs.fundus(1, 3)
main = F[0]
ben = fs.ben_graham(main)
att = fs.attention_map(MASKS)


def rotate(a, deg):
    M = cv2.getRotationMatrix2D((fs.S / 2, fs.S / 2), deg, 1.0)
    return cv2.warpAffine(a, M, (fs.S, fs.S))


def jitter(a):
    b = a.astype(np.float32) * np.array([0.85, 1.05, 1.15]) * 1.12
    return np.clip(b, 0, 255).astype(np.uint8)


def erase(a):
    b = a.copy(); b[300:370, 150:240] = 128
    return b


raw_like = np.zeros((fs.S, int(fs.S * 1.35), 3), np.uint8)
raw_like[:, int(fs.S * 0.175):int(fs.S * 0.175) + fs.S] = main

# ================================================================ PANEL A
rbox(1, 64, 98, 30, PANEL_A, PANEL_A_E, 1.3, r=2.5, z=0)
title_tab(50, 93.4, 'A. Data Preprocessing and Two-Stage Transfer Learning', 46)

# original datasets
rbox(2.5, 66, 13.5, 25, '#ffffff', '#3d6fc4', 1.2, '--', r=1.2, z=1)
txt(9.25, 89.6, 'Original', 11.5, color='#2b56a8'); txt(9.25, 88.0, 'Datasets', 11.5, color='#2b56a8')
for k, a in enumerate([F[2], F[1], F[0]]):
    image(a, 4.2 + (2 - k) * 0.9, 77.6 + (2 - k) * 0.9, 6.6, 6.6, z=5 + k)
txt(9.25, 76.3, 'APTOS-2019', 10.5); txt(9.25, 75.0, '(3,662 images)', 9.5, False)

# IDRiD stack (drawn small)
for k, a in enumerate([F[5], F[4], F[3]]):
    image(a, 4.2 + (2 - k) * 0.8, 67.0 + (2 - k) * 0.8, 5.0, 5.0, z=5 + k)
txt(11.9, 69.6, 'IDRiD', 10.5, ha='left')

# preprocessing
rbox(20, 77.5, 37, 13.5, '#ffffff', '#3d6fc4', 1.2, '--', r=1.2, z=1)
txt(38.5, 89.7, 'Fundus Preprocessing', 11.5, color='#2b56a8')
image(raw_like, 21.5, 79.7, 9.4, 7.0, z=5)
image(main, 35.0, 79.7, 7.0, 7.0, z=5)
image(ben, 46.5, 79.7, 7.0, 7.0, z=5)
txt(26.2, 78.6, 'raw photo', 10, False); txt(38.5, 78.6, 'crop + pad, 448²', 10, False)
txt(50.0, 78.6, 'Ben Graham', 10, False)
arrow(31.1, 83.2, 34.8, 83.2, NAVY, 1.2); arrow(42.2, 83.2, 46.3, 83.2, NAVY, 1.2)

# augmentation
rbox(20, 66, 37, 10.5, '#ffffff', '#3d6fc4', 1.2, '--', r=1.2, z=1)
txt(38.5, 75.2, 'Data Augmentation', 11.5, color='#2b56a8')
augs = [(main[:, ::-1], 'flip'), (rotate(main, 60), 'rotate ±180°'), (jitter(main), 'colour jitter'),
        (erase(main), 'random erasing')]
for i, (a, s) in enumerate(augs):
    image(a, 21.8 + i * 8.9, 68.4, 5.6, 5.6, z=5)
    txt(24.6 + i * 8.9, 67.2, s, 9.5, False)

arrow(16.0, 83.2, 20.0, 83.2, NAVY, 1.3)
path_arrow([(38.5, 77.5), (38.5, 76.5)], NAVY, 1.2)

# two-stage transfer block (like the Poisson-blending block)
rbox(60, 66, 10, 25, PINK, PINK_E, 1.2, '--', r=1.2, z=1)
txt(65, 87.6, 'Stage 1', 11); txt(65, 85.9, 'pre-train', 10, False); txt(65, 84.4, 'on APTOS', 10, False)
txt(65, 82.8, '10 epochs', 9.5, False, color='#555555')
arrow(65, 81.6, 65, 78.6, NAVY, 1.4)
txt(65, 77.0, 'Stage 2', 11); txt(65, 75.3, 'fine-tune', 10, False); txt(65, 73.8, 'on IDRiD', 10, False)
txt(65, 72.2, '5 folds', 9.5, False, color='#555555'); txt(65, 70.7, 'EMA weights', 9.5, False, color='#555555')
txt(65, 68.6, '+ 4-flip TTA', 9.5, False, color='#555555')
arrow(57.0, 83.2, 60.0, 83.2, NAVY, 1.3); arrow(57.0, 71.0, 60.0, 71.0, NAVY, 1.3)

# IDRiD split / CV matrix
rbox(73, 66, 24.5, 25, '#ffffff', '#3d6fc4', 1.2, '--', r=1.2, z=1)
txt(85.25, 89.6, 'IDRiD Partition', 11.5, color='#2b56a8')
cx0, cy0, cw, chh = 77.2, 77.0, 3.0, 1.75
for f in range(5):
    y = cy0 + (4 - f) * (chh + 0.35)
    txt(76.6, y + chh / 2, f'F{f + 1}', 9.5, False, ha='right')
    for c in range(5):
        ax.add_patch(Rectangle((cx0 + c * (cw + 0.3), y), cw, chh, fc=ORANGE if c == f else '#9cc0ef',
                               ec='#555555', lw=0.5, zorder=5))
txt(85.6, 76.0, '85% train + val (5-fold CV)', 9.5, False)
ax.add_patch(Rectangle((cx0, 70.4), 4 * (cw + 0.3) + cw, 3.2, fc='#ffcdd2', ec=RED, lw=1.0, ls='--', zorder=5))
txt(cx0 + (5 * cw + 1.2) / 2, 72.0, '15% held-out test (locked)', 10, True, color=RED)
ax.add_patch(Rectangle((75.3, 67.4), 1.4, 1.0, fc='#9cc0ef', ec='#555555', lw=0.5, zorder=5)); txt(77.0, 67.9, 'train', 9, False, ha='left')
ax.add_patch(Rectangle((81.0, 67.4), 1.4, 1.0, fc=ORANGE, ec='#555555', lw=0.5, zorder=5)); txt(82.7, 67.9, 'val → OOF', 9, False, ha='left')
ax.add_patch(Rectangle((89.0, 67.4), 1.4, 1.0, fc='#ffcdd2', ec=RED, lw=0.5, zorder=5)); txt(90.7, 67.9, 'test', 9, False, ha='left')
arrow(73.0, 78.5, 70.0, 78.5, NAVY, 1.3)

# dotted link A -> B
ax.plot([65, 65], [66, 60.2], ls=(0, (2, 2)), color='#666666', lw=1.2, zorder=3)
ax.plot([65, 4.5], [60.2, 60.2], ls=(0, (2, 2)), color='#666666', lw=1.2, zorder=3)
arrow(4.5, 60.2, 4.5, 58.9, '#666666', 1.2, ls=(0, (2, 2)))

# ================================================================ PANEL B
rbox(1, 1, 98, 61.5, '#ffffff', PANEL_B_E, 1.5, r=3, z=0)
title_tab(50, 62.5, 'B. NITSCI Architecture', 22, ec=PANEL_B_E)

# ---- sub-panel B1: feature stage
rbox(2.5, 41, 95, 17.7, SUB1, SUB1_E, 1.1, '--', r=2, z=1)
txt(4, 57.2, 'The Feature Stage', 11.5, color=ORANGE_E, ha='left', style='italic')
image(main, 4.0, 44.0, 9.0, 9.0, z=5)
txt(8.8, 42.6, r"input $x$, 448$\times$448", 10, True)
fat(13.6, 48.5, 17.0, 48.5, '#6f9ee8', 0.9)

# EfficientNetV2-S as 3-D blocks
heights = [10.0, 8.8, 7.4, 6.0, 4.8, 3.8]
blues = ['#c9dcf7', '#a9c6f0', '#86aee8', '#5f92dc', '#3f78cf', '#2a5fb4']
xb = 17.6
for h, c in zip(heights, blues):
    cuboid(xb, 48.5 - h / 2, 1.6, h, 1.4, c)
    xb += 3.0
txt(26.5, 56.0, 'EfficientNetV2-S', 11.5)
txt(26.5, 42.6, '6 stages, stride 32, ImageNet-21k', 9.5, False)
fat(36.4, 48.5, 39.4, 48.5, '#6f9ee8', 0.9)

# feature maps
fm = fs.feature_maps(main, 6)
for k, a in enumerate(fm[::-1]):
    skew_image(a, 40.0 + k * 0.75, 44.8 + k * 0.0, 4.0, 5.2, z=5 + k, skew=28)
txt(44.6, 42.6, r'$F$: 256$\times$14$\times$14', 10)
fat(49.8, 48.5, 52.4, 48.5, '#6f9ee8', 0.9)

# 1x1 conv block
rbox(52.6, 45.6, 5.2, 5.8, ORANGE, ORANGE_E, 1.0, r=0.6, z=5)
txt(55.2, 49.3, r'1$\times$1', 10.5, color='white'); txt(55.2, 47.6, 'Conv', 10.5, color='white')
txt(55.2, 44.4, 'BN + GELU', 9, False)
fat(58.2, 48.5, 60.6, 48.5, '#6f9ee8', 0.9)

# tokens grid coloured by the image
small = cv2.resize(main, (14, 14), interpolation=cv2.INTER_AREA) / 255.0
token_grid(61.0, 43.6, 9.4, 14, small, ec='#333333')
txt(65.7, 54.2, r'Tokens $T$ ($N$=196, $D$=256)', 10)

# model size (measured)
rbox(74.0, 43.2, 22.0, 12.0, '#ffffff', SUB1_E, 1.0, r=1, z=4)
txt(85.0, 53.6, 'Model size (measured)', 10.5, color='#2e6b2e')
for i, (k, v) in enumerate([('backbone', '19.85 M'), ('cross-expert head', '1.40 M'), ('total', '21.25 M'),
                            (r'GFLOPs (448$^2$)', '23.0')]):
    txt(75.5, 51.4 - i * 2.1, k, 10, False, ha='left'); txt(94.6, 51.4 - i * 2.1, v, 10, i == 2, ha='right')

# ---- sub-panel B2: cross-expert stage
rbox(2.5, 2.5, 95, 37, SUB2, SUB2_E, 1.1, '--', r=2, z=1)
txt(4, 38.0, 'The Cross-Expert Stage', 11.5, color=ORANGE_E, ha='left', style='italic')
ax.plot([65.7, 65.7, 3.0, 3.0], [43.4, 40.2, 40.2, 11.5], color=NAVY, lw=1.3, zorder=15)
txt(64.9, 41.6, r'$T$', 11, False, ha='right')
arrow(10.5, 40.2, 10.5, 34.6, NAVY, 1.3)
arrow(3.0, 11.5, 6.9, 11.5, NAVY, 1.3)

# global expert (Transformer block)
rbox(3.5, 22.5, 14, 12, '#ffffff', PURPLE_E, 1.2, r=1, z=4)
txt(10.5, 33.4, 'Global Expert', 11, color='#3d2a7a')
for i, (s, c) in enumerate([('LayerNorm', '#efe9fb'), ('MHSA (4 heads)', PURPLE), ('LayerNorm', '#efe9fb'),
                            ('FFN (512)', PURPLE)]):
    rbox(4.6, 29.9 - i * 1.95, 11.8, 1.6, c, PURPLE_E, 0.6, r=0.3, z=5)
    txt(10.5, 30.7 - i * 1.95, s, 9, False)
txt(10.5, 23.3, r'$G=\mathrm{TE}(T)$', 10.5, False)

# lesion expert
rbox(3.5, 4.0, 30.5, 16.5, '#ffffff', ORANGE_E, 1.2, r=1, z=4)
txt(18.75, 19.3, 'Lesion Expert (weakly supervised)', 11, color=ORANGE_E)
rbox(7.0, 7.4, 6.4, 8.3, ORANGE, ORANGE_E, 1.0, r=0.5, z=5)
for i, s in enumerate([r'Conv 3$\times$3', 'GELU', r'Conv 1$\times$1', r'$\sigma$']):
    txt(10.2, 14.6 - i * 1.95, s, 9, True, color='white')
txt(10.2, 5.8, 'lesion head', 9.5, False)
arrow(13.6, 11.5, 15.3, 11.5, NAVY, 1.2)
image(fs.overlay(main, att), 15.4, 7.5, 8.0, 8.0, z=5)
txt(19.4, 5.8, r'attention map $m$', 9.5, False)
arrow(23.6, 11.5, 25.1, 11.5, NAVY, 1.2)
ax.add_patch(plt.Circle((26.3, 11.5), 1.1, fc='white', ec=ORANGE_E, lw=1.2, zorder=6))
txt(26.3, 11.45, r'$\odot$', 14, False, color=ORANGE_E)
heat = cm.jet(cv2.resize(att, (14, 14), interpolation=cv2.INTER_AREA))[..., :3]
tok_l = small * 0.45 + heat * 0.55
token_grid(28.4, 8.3, 5.0, 14, tok_l, ec='#333333')
txt(31.1, 14.4, r'$L=T\odot m$', 10.5, False)
arrow(27.4, 11.5, 28.3, 11.5, NAVY, 1.1)
txt(30.9, 5.8, r'sparsity $\lambda_m\overline{m}$', 9.5, False, color='#555555')
arrow(26.3, 15.6, 26.3, 12.7, NAVY, 1.1); txt(26.3, 16.5, r'$T$', 10.5, False)

# cross-attention (network box like the Net1-4 panel)
rbox(37, 4.0, 18, 30.5, '#ffffff', '#7aa6e0', 1.3, r=1.2, z=4)
txt(46, 33.0, 'Bidirectional', 11, color=BLUE_E); txt(46, 31.4, 'Cross-Attention', 11, color=BLUE_E)
rbox(39.5, 23.5, 13, 5.2, ORANGE, ORANGE_E, 1.0, r=0.6, z=5)
txt(46, 27.0, 'MHA', 11, color='white'); txt(46, 25.0, r'$Q{=}G,\;K{=}V{=}L$', 10, False, color='white')
rbox(39.5, 8.5, 13, 5.2, ORANGE, ORANGE_E, 1.0, r=0.6, z=5)
txt(46, 12.0, 'MHA', 11, color='white'); txt(46, 10.0, r'$Q{=}L,\;K{=}V{=}G$', 10, False, color='white')
path_arrow([(17.5, 28.5), (36.0, 28.5), (36.0, 26.1), (39.4, 26.1)], PURPLE_E, 1.4)
path_arrow([(33.4, 11.0), (39.4, 11.0)], ORANGE_E, 1.4)
arrow(40.6, 23.4, 41.6, 13.8, PURPLE_E, 1.1, '--')
arrow(51.4, 13.8, 50.4, 23.4, ORANGE_E, 1.1, '--')
txt(46, 18.6, '+ residual,', 9.5, False); txt(46, 17.1, 'LayerNorm', 9.5, False)
txt(46, 5.6, r"$G'$, $L'$", 10.5, False)

# pooling vectors
fat(55.4, 26.1, 58.0, 26.1, GREEN_ARROW, 0.8)
fat(55.4, 11.0, 58.0, 11.0, GREEN_ARROW, 0.8)
vector(58.4, 22.6, 7, '#b9a6e6', 0.95, label=r'$v_g$')
vector(58.4, 7.6, 7, '#f6b27c', 0.95, label=r'$v_\ell$')
txt(59.0, 31.4, 'mean', 9.5, False); txt(59.0, 16.6, 'm-weighted', 9.5, False); txt(59.0, 15.2, 'mean', 9.5, False)

# adaptive gate (like FAB)
fat(59.7, 26.1, 62.3, 22.0, GREEN_ARROW, 0.8)
fat(59.7, 11.0, 62.3, 15.0, GREEN_ARROW, 0.8)
rbox(62.3, 6.5, 7.6, 24.5, PINK, PINK_E, 1.2, '--', r=1, z=4)
txt(66.1, 24.8, 'Adaptive', 10.5); txt(66.1, 23.2, 'Gate', 10.5)
txt(66.1, 19.0, r'$g=\sigma(w^T$', 10, False); txt(66.1, 17.2, r'$[v_g;v_\ell])$', 10, False)
txt(66.1, 12.6, r'$z=$GELU(', 9.5, False); txt(66.1, 11.0, r'$gW_Gv_g+$', 9.5, False)
txt(66.1, 9.4, r'$(1{-}g)W_\ell v_\ell)$', 9.5, False)

# heads
fat(70.1, 16.8, 71.7, 16.8, GREEN_ARROW, 0.8)
vector(72.0, 13.5, 7, '#a7dba0', 0.95, label=r'$z$')
path_arrow([(72.3, 20.2), (72.3, 29.0), (75.5, 29.0)], NAVY, 1.2)
path_arrow([(73.2, 20.2), (73.2, 22.0), (75.5, 22.0)], NAVY, 1.2)
rbox(75.6, 26.6, 9.6, 4.8, LBLUE, BLUE_E, 1.0, r=0.6, z=5)
txt(80.4, 29.6, 'Classification', 10); txt(80.4, 27.9, 'head', 10)
rbox(75.6, 19.6, 9.6, 4.8, LBLUE, BLUE_E, 1.0, r=0.6, z=5)
txt(80.4, 22.6, 'Regression', 10); txt(80.4, 20.9, 'head', 10)
probs = [0.04, 0.06, 0.20, 0.62, 0.08]
for i, pv in enumerate(probs):
    ax.add_patch(Rectangle((86.6 + i * 1.95, 26.6), 1.4, pv * 9, fc='#4a7fd4' if i == 3 else '#a9c6f0', ec='#333333',
                           lw=0.4, zorder=5))
    txt(87.3 + i * 1.95, 25.7, str(i), 8.5, False)
txt(91.2, 33.0, r'$p$ (grades 0-4)', 10, False)
ax.plot([86.6, 94.6], [22.0, 22.0], color=NAVY, lw=1.0, zorder=5)
for i in range(5):
    ax.plot([86.6 + i * 2.0] * 2, [21.6, 22.4], color=NAVY, lw=0.8, zorder=5); txt(86.6 + i * 2.0, 20.8, str(i), 8.5, False)
ax.add_patch(plt.Circle((86.6 + 2.8 * 2.0, 22.0), 0.45, fc=RED, ec='none', zorder=6))
txt(90.6, 23.7, r'$r=2.8$', 10, False)
arrow(85.4, 29.0, 86.4, 29.0, NAVY, 1.0); arrow(85.4, 22.0, 86.4, 22.0, NAVY, 1.0)

# grade score
rbox(76.0, 8.4, 19.4, 8.6, '#fff5d6', '#c79a2a', 1.2, r=0.8, z=4)
txt(85.7, 15.6, r'$s=\frac{1}{2}\sum_k k\,p_k+\frac{1}{2}r$', 10.5, False)
ax.plot([77.2, 94.2], [11.9, 11.9], color=NAVY, lw=1.0, zorder=5)
for i in range(5):
    ax.plot([77.2 + i * 4.25] * 2, [11.5, 12.3], color=NAVY, lw=0.8, zorder=5); txt(77.2 + i * 4.25, 10.7, str(i), 8.5, False)
for j, t in enumerate([0.55, 1.45, 2.5, 3.4]):
    ax.plot([77.2 + t * 4.25] * 2, [11.9, 13.5], color=RED, lw=1.0, zorder=5)
    txt(77.2 + t * 4.25, 14.1, rf'$\theta_{j + 1}$', 9, False, color=RED)
s_val = 0.5 * sum(k * p for k, p in enumerate(probs)) + 0.5 * 2.8
xs_ = 77.2 + s_val * 4.25
ax.add_patch(Polygon([(xs_ - 0.5, 12.9), (xs_ + 0.5, 12.9), (xs_, 12.0)], fc=NAVY, zorder=6))
txt(85.7, 9.3, 'thresholds fitted on OOF data', 9, False, color='#555555')
path_arrow([(95.8, 29.0), (96.9, 29.0), (96.9, 10.0), (95.5, 10.0)], NAVY, 1.0)
path_arrow([(94.8, 22.0), (96.2, 22.0), (96.2, 14.5), (95.5, 14.5)], NAVY, 1.0)

# outputs
arrow(85.7, 8.4, 85.7, 7.0, '#1b5e20', 1.2)
txt(85.7, 6.0, r'$\Rightarrow$ Grade 3 (severe NPDR)', 10.5, True, color='#1b5e20')
txt(85.7, 4.2, r'Referable: $p_2{+}p_3{+}p_4\geq$ cut-off', 9.5, False, color='#1b5e20')

out = os.path.join(HERE, '..', 'nitsci_method')
fig.savefig(out + '.pdf')
fig.savefig(out + '.png', dpi=300)
print('saved', out + '.pdf/.png')
