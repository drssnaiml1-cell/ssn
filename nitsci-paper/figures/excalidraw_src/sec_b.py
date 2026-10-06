from lib import *

Y0 = 500
# ---------------- Panel B frame ----------------
rect(0, Y0, 1920, 720, '#f0fdf4', GREEN_S, 2, 'dashed', round_=False)
text(20, Y0 + 12, 'B. NITSCI: cross-expert lesion-aware network with ordinal dual head', 24, TITLE)

# input
fundus(95, 830, 65)
text(20, 905, 'input x\n3 × 448 × 448', 16, ONLIGHT, 'center', w=150)
arrow([(162, 830), (198, 830)], NAVY, 2)

# backbone: shrinking stages
heights = [220, 185, 150, 115, 85]
fills = [BLUE4, BLUE3, BLUE2, BLUE, NAVY]
for i, (h, f) in enumerate(zip(heights, fills)):
    rect(200 + i * 36, 830 - h / 2, 28, h, f, NAVY, 1, round_=False)
text(175, 690, 'EfficientNetV2-S', 18, NAVY, 'center', w=240)
text(175, 948, 'ImageNet-21k init\n19.85 M params', 14, BODY, 'center', w=240)
arrow([(370, 830), (412, 830)], NAVY, 2)

# feature map
for k in (2, 1, 0):
    rect(415 + 8 * k, 795 - 8 * k, 66, 66, BLUE3 if k else BLUE2, NAVY, 1, round_=False)
text(395, 880, 'F: 256 × 14 × 14', 14, BODY, 'center', w=130)
arrow([(500, 830), (532, 830)], NAVY, 2)

# projection
p = box(535, 800, 115, 60, '1×1 conv\nBN, GELU', BLUE4, NAVY, 14)
text(535, 866, 'D = 256', 14, BODY, 'center', w=115)
arrow([(650, 830), (680, 830)], NAVY, 2)

# tokens
grid(683, 788, 7, 12)
text(650, 758, 'tokens T, N = 196', 14, BODY, 'center', w=150)

# fan-out to the two experts
arrow([(767, 815), (800, 815), (800, 695), (840, 695)], NAVY, 2)
arrow([(767, 845), (800, 845), (800, 935), (840, 935)], NAVY, 2)
arrow([(725, 872), (725, 1010), (1120, 1010), (1120, 952)], NAVY, 2)

# global expert
g = box(840, 655, 240, 80, 'Global expert\nTransformer layer, 4 heads', PUR_F, PUR_S, 16)
text(1088, 668, 'G', 18, PUR_S)

# lesion pathway
lh = box(840, 900, 150, 70, 'lesion head\n3×3 conv, 1×1 conv\nsigmoid', ORANGE_F, ORANGE_S, 13)
arrow([(990, 935), (1003, 935)], ORANGE_S, 2)
grid(1005, 893, 7, 12, hot={(1, 2), (2, 2), (4, 4), (5, 1)}, warm={(1, 3), (2, 1), (4, 3), (3, 4), (5, 2)},
     fill='#fff7ed', stroke=ORANGE_S)
text(990, 980, 'lesion map m', 14, ORANGE_S, 'center', w=110)
arrow([(1089, 935), (1104, 935)], ORANGE_S, 2)
ellipse(1104, 919, 32, 32, '#ffffff', ORANGE_S, 2)
text(1104, 920, '⊙', 22, ORANGE_S, 'center', w=32)
text(1080, 878, 'L = T ⊙ m', 14, ORANGE_S)

# cross-attention block
rect(1170, 620, 215, 385, '#ffffff', PUR_S, 2, 'dashed', round_=False)
text(1170, 628, 'bidirectional cross-attention', 14, PUR_S, 'center', w=215)
box(1190, 660, 180, 70, 'MHA\nQ = G,  K = V = L', PUR_F, PUR_S, 14)
box(1190, 900, 180, 70, 'MHA\nQ = L,  K = V = G', ORANGE_F, ORANGE_S, 14)
arrow([(1080, 695), (1190, 695)], PUR_S, 2)
arrow([(1136, 935), (1190, 935)], ORANGE_S, 2)
arrow([(1150, 695), (1150, 765), (1240, 765), (1240, 900)], PUR_S, 1.5, 'dashed')
arrow([(1160, 935), (1160, 810), (1320, 810), (1320, 730)], ORANGE_S, 1.5, 'dashed')
text(1170, 975, '+ residual, LayerNorm', 14, BODY, 'center', w=215)

# pooling
arrow([(1370, 695), (1575, 695), (1575, 755)], PUR_S, 2)
text(1395, 668, 'mean → v_g', 15, PUR_S)
arrow([(1370, 935), (1575, 935), (1575, 879)], ORANGE_S, 2)
text(1395, 908, 'm-weighted mean → v_ℓ', 15, ORANGE_S)

# gate
gd = diamond(1470, 755, 210, 124, YEL_F, YEL_S)
label(gd, 'adaptive gate\ng = σ(w·[v_g; v_ℓ])', 14)
text(1395, 965, 'z = GELU(g·W_G v_g + (1 − g)·W_ℓ v_ℓ)', 14, YEL_S)
arrow([(1680, 817), (1700, 817)], YEL_S, 2)
zb = box(1700, 792, 60, 50, 'z', GREEN_F, GREEN_S, 18)

# heads
ch = box(1680, 655, 210, 48, 'classification head', BLUE3, NAVY, 15)
rh = box(1680, 930, 210, 48, 'regression head', BLUE3, NAVY, 15)
arrow([(1730, 792), (1730, 703)], GREEN_S, 2)
arrow([(1730, 842), (1730, 930)], GREEN_S, 2)
for i, h in enumerate([10, 18, 46, 14, 6]):
    rect(1700 + i * 34, 640 - h * 1.4 - 2, 24, h * 1.4, BLUE if i == 2 else BLUE3, NAVY, 1, round_=False)
    text(1700 + i * 34, 640, str(i), 13, BODY, 'center', w=24)
text(1590, 600, 'p (grades 0-4)', 14, NAVY)
text(1740, 880, 'r (+2 offset)', 14, NAVY)
arrow([(1890, 679), (1903, 679), (1903, 1120), (1890, 1120)], NAVY, 2)
arrow([(1785, 978), (1785, 1070)], NAVY, 2)

# decision
dbox = rect(1440, 1070, 450, 130, YEL_F, YEL_S, 2)
text(1440, 1078, 'grade score  s = ½ Σ k·p_k + ½ r', 15, ONLIGHT, 'center', w=450)
line([(1475, 1140), (1855, 1140)], NAVY, 2)
for k in range(5):
    x = 1475 + k * 95
    line([(x, 1134), (x, 1146)], NAVY, 2)
    text(x - 10, 1150, str(k), 13, BODY, 'center', w=20)
for j, x in enumerate([1520, 1620, 1715, 1805]):
    line([(x, 1118), (x, 1140)], RED_S, 2)
    text(x - 14, 1098, f'θ{j+1}', 14, RED_S, 'center', w=28)
text(1440, 1172, 'θ1…θ4 fitted on out-of-fold data (panel A)', 14, BODY, 'center', w=450)

# outputs
o1 = ellipse(1170, 1085, 230, 70, GREEN_F, GREEN_S, 2)
label(o1, 'predicted grade\n0 / 1 / 2 / 3 / 4', 15)
arrow([(1440, 1120), (1400, 1120)], GREEN_S, 2)
o2 = ellipse(890, 1085, 255, 70, GREEN_F, GREEN_S, 2)
label(o2, 'referable DR\np2 + p3 + p4 ≥ cut-off', 15)
arrow([(1500, 1200), (1500, 1212), (1018, 1212), (1018, 1155)], GREEN_S, 2)

# inference ensemble and loss (training)
box(450, 1080, 400, 100, 'inference: 5 fold models × 4 flips\n= 20 predictions averaged\n(evaluated once on the locked test set)',
    BLUE4, NAVY, 14)
box(20, 1080, 400, 100, 'training loss\nCE(class-weighted, smoothing 0.05)\n+ 0.5·SmoothL1(r, y) + 0.01·mean(m)',
    RED_F, RED_S, 14)
