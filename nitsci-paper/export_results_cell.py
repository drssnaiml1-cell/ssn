# =====================================================================
#  NITSCI paper: results export cell
#  Paste this as the LAST cell of NITSCI_v2_high_accuracy.ipynb and run it
#  after the notebook has finished. It writes:
#     results_<TAG>.json      every number the paper needs (+ per-image preds)
#     figures/*.pdf|png       the figures the paper includes
#  For ablation runs, change RUN_TAG (see README.md) and re-run the notebook.
# =====================================================================
import json, platform
from scipy.stats import binomtest

RUN_TAG = 'full'          # 'full', 'noaptos', 'clahe', 'noreg', 'nocross', 'nogate', 'nolesion', 'plain'
N_BOOT  = 2000
os.makedirs('figures', exist_ok=True)
rng = np.random.RandomState(SEED)

def boot_ci(fn, *arrays, n=N_BOOT):
    """Percentile 95% bootstrap CI over test images."""
    vals, N = [], len(arrays[0])
    for _ in range(n):
        ix = rng.randint(0, N, N)
        try:
            vals.append(fn(*[a[ix] for a in arrays]))
        except ValueError:
            pass
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]

R = {'tag': RUN_TAG, 'backbone': BACKBONE, 'img_size': IMG_SIZE, 'preproc': PREPROC,
     'use_aptos': bool(USE_APTOS), 'reg_weight': REG_WEIGHT, 'n_folds': N_FOLDS,
     'idrid_epochs': IDRID_EPOCHS, 'aptos_epochs': APTOS_EPOCHS if USE_APTOS else 0,
     'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu',
     'torch': torch.__version__, 'timm': timm.__version__, 'python': platform.python_version()}

# ---- data -----------------------------------------------------------
R['n_idrid'] = int(len(idrid_y)); R['n_trainval'] = int(len(trainval_idx)); R['n_test'] = int(len(test_idx))
R['idrid_counts'] = np.bincount(idrid_y, minlength=NUM_CLASSES).tolist()
R['test_counts'] = np.bincount(y_test, minlength=NUM_CLASSES).tolist()
if USE_APTOS:
    R['n_aptos'] = int(len(aptos_y)); R['aptos_counts'] = np.bincount(aptos_y, minlength=NUM_CLASSES).tolist()

# ---- model size and speed ------------------------------------------
_mm = CrossExpertDRNet(pretrained=False).to(device).eval()
R['params_M'] = sum(p.numel() for p in _mm.parameters()) / 1e6
R['params_backbone_M'] = sum(p.numel() for p in _mm.backbone.parameters()) / 1e6
if device.type == 'cuda':
    xb = torch.randn(BATCH_SIZE, 3, IMG_SIZE, IMG_SIZE, device=device)
    with torch.no_grad(), torch.autocast('cuda', dtype=torch.float16):
        for _ in range(3): _mm(xb)
        torch.cuda.synchronize(); t0 = time.time()
        for _ in range(10): _mm(xb)
        torch.cuda.synchronize()
    R['ms_per_image'] = (time.time() - t0) / (10 * BATCH_SIZE) * 1000
del _mm; torch.cuda.empty_cache()

# ---- 5-class grading (main result) --------------------------------
R['grading'] = {k: float(v) for k, v in m5.items()}
R['decision_rule'] = best_rule
R['thresholds'] = [float(t) for t in thr_opt]
R['oof_rules'] = {k: float(v) for k, v in rule_results.items()}
R['test_rules'] = {k: float(accuracy_score(y_test, f(test_p, test_r))) for k, f in candidates.items()}
R['test_rules_qwk'] = {k: float(cohen_kappa_score(y_test, f(test_p, test_r), weights='quadratic'))
                       for k, f in candidates.items()}
R['confusion5'] = confusion_matrix(y_test, pred_test, labels=LABELS).tolist()
R['per_class'] = {
    'precision': precision_score(y_test, pred_test, labels=LABELS, average=None, zero_division=0).tolist(),
    'recall': recall_score(y_test, pred_test, labels=LABELS, average=None, zero_division=0).tolist(),
    'f1': f1_score(y_test, pred_test, labels=LABELS, average=None, zero_division=0).tolist(),
    'support': np.bincount(y_test, minlength=NUM_CLASSES).tolist()}
R['ci'] = {
    'acc5': boot_ci(lambda a, b: accuracy_score(a, b), y_test, pred_test),
    'qwk5': boot_ci(lambda a, b: cohen_kappa_score(a, b, weights='quadratic'), y_test, pred_test),
    'f1macro5': boot_ci(lambda a, b: f1_score(a, b, average='macro', zero_division=0), y_test, pred_test),
}

# ---- referable DR ---------------------------------------------------
R['referable'] = {k: float(v) for k, v in m2.items()}
R['confusion2'] = [[int(tn), int(fp)], [int(fn), int(tp)]]
R['ci']['ref_acc'] = boot_ci(lambda a, b: np.mean(a == b), yb_test, pb_test)
R['ci']['ref_sens'] = boot_ci(lambda a, b: np.mean(b[a == 1] == 1), yb_test, pb_test)
R['ci']['ref_spec'] = boot_ci(lambda a, b: np.mean(b[a == 0] == 0), yb_test, pb_test)
R['ci']['ref_auc'] = boot_ci(lambda a, s: roc_auc_score(a, s), yb_test, ref_test)

# ---- OOF (cross-validation) summary --------------------------------
oof_pred = decide(oof_p, oof_r)
R['oof'] = {'acc5': float(accuracy_score(y_oof, oof_pred)),
            'qwk5': float(cohen_kappa_score(y_oof, oof_pred, weights='quadratic')),
            'ref_auc': float(roc_auc_score(yb_oof, ref_oof))}
fold_acc, fold_qwk = [], []
for tr, va in skf.split(trainval_idx, idrid_y[trainval_idx]):
    p_ = decide(oof_p[va], oof_r[va])
    fold_acc.append(accuracy_score(y_oof[va], p_)); fold_qwk.append(cohen_kappa_score(y_oof[va], p_, weights='quadratic'))
R['oof']['fold_acc'] = [float(v) for v in fold_acc]; R['oof']['fold_qwk'] = [float(v) for v in fold_qwk]
R['epochs_run'] = [len(h['val_acc']) for h in fold_hists]

# ---- inference ablations: TTA and ensembling (no retraining) -------
single_acc, single_qwk, noTTA_p, noTTA_r = [], [], [], []
for k in range(N_FOLDS):
    mk = CrossExpertDRNet(pretrained=False).to(device)
    mk.load_state_dict(torch.load(f'idrid_fold{k + 1}.pth', map_location=device))
    p1, r1 = predict(mk, idrid_imgs, test_idx, tta=False); noTTA_p.append(p1); noTTA_r.append(r1)
    pk, rk = predict(mk, idrid_imgs, test_idx, tta=True)
    yk = decide(pk, rk)
    single_acc.append(accuracy_score(y_test, yk)); single_qwk.append(cohen_kappa_score(y_test, yk, weights='quadratic'))
    del mk; torch.cuda.empty_cache()
pn = decide(np.mean(noTTA_p, 0), np.mean(noTTA_r, 0))
R['inference_ablation'] = {
    'single_fold_acc_mean': float(np.mean(single_acc)), 'single_fold_acc_std': float(np.std(single_acc)),
    'single_fold_qwk_mean': float(np.mean(single_qwk)), 'single_fold_qwk_std': float(np.std(single_qwk)),
    'ensemble_noTTA_acc': float(accuracy_score(y_test, pn)),
    'ensemble_noTTA_qwk': float(cohen_kappa_score(y_test, pn, weights='quadratic')),
    'ensemble_TTA_acc': float(m5['Accuracy']), 'ensemble_TTA_qwk': float(m5['Quadratic weighted kappa'])}

# ---- per-image predictions (for McNemar tests between runs) --------
R['test_idx'] = [int(i) for i in test_idx]
R['y_test'] = [int(v) for v in y_test]
R['pred_test'] = [int(v) for v in pred_test]
R['ref_pred_test'] = [int(v) for v in pb_test]
R['ref_score_test'] = [float(v) for v in ref_test]

with open(f'results_{RUN_TAG}.json', 'w') as f:
    json.dump(R, f, indent=1)
print(f'Saved results_{RUN_TAG}.json')

# ---- figures (full run only) ---------------------------------------
if RUN_TAG == 'full':
    plt.rcParams.update({'font.size': 11, 'savefig.bbox': 'tight'})
    fig, ax = plt.subplots(1, 2, figsize=(12, 3.6))
    for a, (name, yy) in zip(ax, [('IDRiD', idrid_y)] + ([('APTOS-2019', aptos_y)] if USE_APTOS else [])):
        a.bar(range(NUM_CLASSES), np.bincount(yy, minlength=NUM_CLASSES), color='#0E2240')
        a.set_xticks(range(NUM_CLASSES)); a.set_xticklabels(GRADE_NAMES, rotation=15)
        a.set_title(f'{name} (n={len(yy)})'); a.set_ylabel('images')
    fig.savefig('figures/distribution.pdf'); plt.close(fig)

    fig, ax = plt.subplots(1, 4, figsize=(14, 3.6))
    for a, j in zip(ax, [np.where(idrid_y == g)[0][0] for g in (0, 2, 3, 4)]):
        a.imshow(cv2.resize(cv2.cvtColor(cv2.imread(idrid_df.img_path[j]), cv2.COLOR_BGR2RGB), (IMG_SIZE, IMG_SIZE)))
        a.set_title(f'raw, grade {idrid_y[j]}'); a.axis('off')
    fig.savefig('figures/samples_raw.png', dpi=150); plt.close(fig)
    fig, ax = plt.subplots(1, 4, figsize=(14, 3.6))
    for a, j in zip(ax, [np.where(idrid_y == g)[0][0] for g in (0, 2, 3, 4)]):
        a.imshow(idrid_imgs[j]); a.set_title(f'{PREPROC}, grade {idrid_y[j]}'); a.axis('off')
    fig.savefig('figures/samples_pre.png', dpi=150); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    sns.heatmap(confusion_matrix(y_test, pred_test, labels=LABELS), annot=True, fmt='d', cmap='Blues', ax=ax[0],
                xticklabels=GRADE_NAMES, yticklabels=GRADE_NAMES, cbar=False)
    ax[0].set_xlabel('Predicted'); ax[0].set_ylabel('True'); ax[0].set_title('(a) 5-class grading')
    sns.heatmap(np.array([[tn, fp], [fn, tp]]), annot=True, fmt='d', cmap='Greens', ax=ax[1], cbar=False,
                xticklabels=['Non-ref.', 'Referable'], yticklabels=['Non-ref.', 'Referable'])
    ax[1].set_xlabel('Predicted'); ax[1].set_ylabel('True'); ax[1].set_title('(b) Referable DR')
    fig.savefig('figures/confusion.pdf'); plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.6, 5))
    yb5 = label_binarize(y_test, classes=LABELS)
    for i in LABELS:
        if yb5[:, i].sum():
            f_, t_, _ = roc_curve(yb5[:, i], test_p[:, i]); ax.plot(f_, t_, label=f'{GRADE_NAMES[i]} (AUC {auc(f_, t_):.3f})')
    f_, t_, _ = roc_curve(yb_test, ref_test); ax.plot(f_, t_, 'k-', lw=2.5, label=f'Referable (AUC {auc(f_, t_):.3f})')
    ax.plot([0, 1], [0, 1], 'k:'); ax.set_xlabel('False positive rate'); ax.set_ylabel('True positive rate')
    ax.legend(fontsize=8, loc='lower right'); fig.savefig('figures/roc.pdf'); plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(15, 3.8))
    for k, key in enumerate(['train_loss', 'val_acc', 'val_qwk']):
        for f, h in enumerate(fold_hists):
            ax[k].plot(np.arange(1, len(h[key]) + 1), h[key], label=f'fold {f + 1}')
        ax[k].set_title(key.replace('_', ' ')); ax[k].set_xlabel('epoch'); ax[k].grid(alpha=0.3)
    ax[0].legend(fontsize=8); fig.savefig('figures/curves.pdf'); plt.close(fig)

    show = np.random.RandomState(0).choice(len(test_idx), 4, replace=False)
    fig, axes = plt.subplots(3, 4, figsize=(14, 10.5))
    for c_, k in enumerate(show):
        j = test_idx[k]; x = eval_tf(idrid_imgs[j]).unsqueeze(0).to(device)
        with torch.no_grad():
            _, _, mask, g = cam_model(x)
        heat = cam(input_tensor=x, targets=[ClassifierOutputTarget(int(pred_test[k]))])[0]
        orig = cv2.resize(cv2.cvtColor(cv2.imread(idrid_df.img_path[j]), cv2.COLOR_BGR2RGB), (IMG_SIZE, IMG_SIZE))
        axes[0, c_].imshow(orig); axes[0, c_].set_title(f'true {y_test[k]} / pred {pred_test[k]}')
        axes[1, c_].imshow(show_cam_on_image(idrid_imgs[j].astype(np.float32) / 255, heat, use_rgb=True))
        axes[1, c_].set_title('Grad-CAM')
        axes[2, c_].imshow(orig); axes[2, c_].imshow(mask[0, 0].cpu().numpy(), cmap='jet', alpha=0.45)
        axes[2, c_].set_title(f'lesion attention (g={g.item():.2f})')
        for a in axes[:, c_]: a.axis('off')
    fig.savefig('figures/explain.png', dpi=130); plt.close(fig)
    print('Saved figures/*.pdf, figures/*.png')

# Download results_*.json and the figures/ folder, put them in nitsci-paper/, then run:
#   python fill_results.py && pdflatex nitsci_paper && bibtex nitsci_paper && pdflatex nitsci_paper && pdflatex nitsci_paper
