# =====================================================================
#  NITSCI paper: architecture ablations
#  Paste this cell directly AFTER the model cell (section 5) of the notebook,
#  set VARIANT, and run the rest of the notebook unchanged. Then run the
#  export cell with RUN_TAG = VARIANT.
#
#    'nocross'  : no bidirectional cross-attention (G and L are not exchanged)
#    'nogate'   : fixed 0.5/0.5 fusion instead of the adaptive gate
#    'nolesion' : no lesion-attention map (lesion expert sees all tokens equally)
#    'plain'    : EfficientNetV2-S + global average pooling + the same dual head
#
#  Data/pre-processing ablations need no code, only a config change in cell 2:
#    'noaptos'  : USE_APTOS = False
#    'clahe'    : PREPROC = 'clahe'
#    'noreg'    : REG_WEIGHT = 0.0
#
#  IMPORTANT: for every variant except 'noaptos' and 'noreg', delete (or rename)
#  aptos_pretrained.pth before running, so that APTOS pretraining is redone for
#  the changed architecture / pre-processing. ('noreg' should also redo it if you
#  want the regression head absent in pretraining too; state which you did.)
# =====================================================================
VARIANT = 'nocross'

_FullNet = CrossExpertDRNet


class AblatedNet(_FullNet):
    def __init__(self, *args, variant=VARIANT, **kw):
        super().__init__(*args, **kw)
        self.variant = variant

    def forward(self, x):
        f = self.proj(self.tap(self.backbone(x)[-1]))
        B, D, h, w = f.shape
        tokens = f.flatten(2).transpose(1, 2)
        if self.variant == 'nolesion':
            m = torch.ones(B, 1, h, w, device=x.device, dtype=f.dtype)
        else:
            m = torch.sigmoid(self.lesion_head(f))
        wts = m.flatten(2).transpose(1, 2)
        G = self.global_expert(tokens)
        L = tokens * wts
        if self.variant != 'nocross':
            Zg, _ = self.g2l(G, L, L)
            Zl, _ = self.l2g(L, G, G)
            G, L = self.norm_g(G + Zg), self.norm_l(L + Zl)
        else:
            G, L = self.norm_g(G), self.norm_l(L)
        v_g = G.mean(1)
        v_l = (L * wts).sum(1) / (wts.sum(1) + 1e-6)
        if self.variant == 'nogate':
            g = torch.full((B, 1), 0.5, device=x.device, dtype=v_g.dtype)
        else:
            g = torch.sigmoid(self.gate(torch.cat([v_g, v_l], -1)))
        fused = F.gelu(g * self.W_G(v_g) + (1 - g) * self.W_L(v_l))
        logits = self.cls_head(fused)
        reg = self.reg_head(fused).squeeze(-1) + 2.0
        mask = F.interpolate(m, size=x.shape[-2:], mode='bilinear', align_corners=False)
        return logits, reg, mask, g


class PlainNet(nn.Module):
    """Baseline: same backbone, global average pooling, same dual head and losses."""
    def __init__(self, backbone=BACKBONE, num_classes=NUM_CLASSES, dim=256, pretrained=True):
        super().__init__()
        self.backbone = timm.create_model(backbone, pretrained=pretrained, features_only=True)
        c = self.backbone.feature_info.channels()[-1]
        self.tap = nn.Identity()
        self.proj = nn.Sequential(nn.Conv2d(c, dim, 1), nn.BatchNorm2d(dim), nn.GELU())
        self.cls_head = nn.Sequential(nn.LayerNorm(dim), nn.Dropout(0.3), nn.Linear(dim, num_classes))
        self.reg_head = nn.Sequential(nn.LayerNorm(dim), nn.Dropout(0.3), nn.Linear(dim, 1))

    def forward(self, x):
        f = self.proj(self.tap(self.backbone(x)[-1]))
        v = f.mean((2, 3))
        B = x.shape[0]
        mask = torch.zeros(B, 1, *x.shape[-2:], device=x.device)    # no lesion map; sparsity term is 0
        return self.cls_head(v), self.reg_head(v).squeeze(-1) + 2.0, mask, torch.zeros(B, 1, device=x.device)


if VARIANT == 'plain':
    CrossExpertDRNet = PlainNet
else:
    CrossExpertDRNet = lambda *a, **k: AblatedNet(*a, **k)

print('Ablation variant:', VARIANT)
