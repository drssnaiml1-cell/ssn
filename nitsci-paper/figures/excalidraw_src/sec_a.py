from lib import *

# ---------------- Panel A frame ----------------
rect(0, 0, 1920, 475, '#eef4ff', SUB, 2, 'dashed', round_=False)
text(20, 12, 'A. Data preparation and two-stage transfer learning', 24, TITLE, bold=True)

# datasets (stacks of stylised fundus images)
for k in (2, 1, 0):
    fundus(95 + 9 * k, 135 + 9 * k, 52, lesions=(k == 0))
text(20, 205, 'APTOS-2019\n3,662 graded images', 16, ONLIGHT, 'center', w=170)
for k in (2, 1, 0):
    fundus(95 + 9 * k, 330 + 9 * k, 52, lesions=(k == 0))
text(20, 400, 'IDRiD\ngrades 0-4', 16, ONLIGHT, 'center', w=170)

# pre-processing timeline
rect(205, 55, 350, 395, '#ffffff', ORANGE_S, 2, 'dashed', round_=False)
text(205, 65, 'Pre-processing (both datasets)', 18, ORANGE_S, 'center', w=350)
line([(235, 118), (235, 398)], ORANGE_S, 2)
steps = ['crop black border (grey > 10)', 'zero-pad to square', 'resize to 448 × 448',
         'Ben Graham:  4I − 4(G_σ ∗ I) + 128', 'circular mask, r = 0.48 × 448']
for i, s in enumerate(steps):
    y = 112 + i * 70
    ellipse(228, y, 14, 14, ORANGE_S, ORANGE_S, 1)
    text(255, y - 3, s, 16, ONLIGHT)
text(255, 345, 'G_σ: Gaussian blur, σ = 448/30', 14, BODY)
arrow([(170, 140), (205, 140)], NAVY, 2)
arrow([(170, 335), (205, 335)], NAVY, 2)

# stage 1
s1 = box(640, 70, 300, 125, 'Stage 1: pretraining\nfull NITSCI model on APTOS\n10 epochs, lr 3×10⁻⁴, EMA 0.999',
         PUR_F, PUR_S, 16)
text(640, 202, '90/10 split for checkpoint selection', 14, BODY, 'center', w=300)
arrow([(555, 135), (640, 135)], NAVY, 2)

# IDRiD split
d = diamond(640, 285, 150, 100, YEL_F, YEL_S)
label(d, 'stratified\nsplit', 15)
arrow([(555, 335), (640, 335)], NAVY, 2)

# folds (85 %)
text(860, 262, '85%: five stratified folds', 15, ONLIGHT)
for i in range(5):
    rect(865 + i * 44, 292, 36, 36, ORANGE_F if i == 4 else BLUE3, NAVY, 1)
text(865, 333, 'train ×4 + val ×1 (rotates)', 14, BODY)
arrow([(790, 335), (820, 335), (820, 310), (865, 310)], NAVY, 2)

# test (15 %)
t = box(865, 385, 230, 52, '15% test: locked away', RED_F, RED_S, 16, RED_S, 'dashed')
arrow([(715, 385), (715, 411), (865, 411)], RED_S, 2)

# stage 2
s2 = box(1230, 270, 280, 120, 'Stage 2: fine-tune ×5 folds\nlr 2×10⁻⁴, EMA 0.99\n≤ 25 epochs, patience 8', PUR_F, PUR_S, 16)
arrow([(1085, 310), (1230, 310)], NAVY, 2)
arrow([(940, 132), (1370, 132), (1370, 270)], PUR_S, 2)
text(1060, 105, 'initialise from stage-1 weights', 14, PUR_S)
text(1215, 397, 'flips, rotation ±180°, colour jitter, random erasing', 14, BODY)

# OOF
o = box(1610, 255, 270, 150, 'out-of-fold predictions\n→ decision rule\n→ grade thresholds θ1…θ4\n→ referral cut-off (Youden J)', YEL_F, YEL_S, 15)
arrow([(1510, 330), (1610, 330)], NAVY, 2)
