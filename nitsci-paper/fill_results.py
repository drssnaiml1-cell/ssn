"""Fill the paper's result slots from the notebook exports.

Reads results_<tag>.json files (written by export_results_cell.py) from this
folder and writes results.tex, which nitsci_paper.tex loads. Every slot that
has no value stays visible in the PDF as a red [key] marker, so nothing can
be submitted with a missing number by accident.

Usage:  python fill_results.py
"""
import glob
import json
import os
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ABLATION_TAGS = ['plain', 'noaptos', 'clahe', 'noreg', 'nolesion', 'nocross', 'nogate']
RULE_KEYS = {'argmax': 'argmax', 'rounded score': 'rounded', 'optimised thresholds': 'opt'}


def pct(v):
    return f'{100 * v:.2f}'


def k3(v):
    return f'{v:.3f}'


def ci_pct(c):
    return f'[{100 * c[0]:.1f}, {100 * c[1]:.1f}]'


def ci_k3(c):
    return f'[{c[0]:.3f}, {c[1]:.3f}]'


def mcnemar_exact(y, a, b):
    """Two-sided exact McNemar test on per-image correctness of two prediction vectors."""
    n01 = sum(1 for t, p, q in zip(y, a, b) if p == t and q != t)
    n10 = sum(1 for t, p, q in zip(y, a, b) if p != t and q == t)
    n = n01 + n10
    if n == 0:
        return 1.0, n01, n10
    k = min(n01, n10)
    p = 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(p, 1.0), n01, n10


def fmt_p(p):
    return '$<$0.001' if p < 0.001 else f'{p:.3f}'


def main():
    runs = {}
    for f in glob.glob(os.path.join(HERE, 'results_*.json')):
        with open(f) as fh:
            r = json.load(fh)
        runs[r['tag']] = r
    if 'full' not in runs:
        print('No results_full.json found: results.tex will contain no values (all slots stay red).')

    out = {}
    full = runs.get('full')
    if full:
        g, rf, ci = full['grading'], full['referable'], full['ci']
        out.update({
            'nidrid': full['n_idrid'], 'ntrainval': full['n_trainval'], 'ntest': full['n_test'],
            'naptos': full.get('n_aptos', '--'), 'gpu': full['gpu'],
            'params': f"{full['params_M']:.2f}", 'paramsbb': f"{full['params_backbone_M']:.2f}",
            'mspi': f"{full['ms_per_image']:.1f}" if 'ms_per_image' in full else '--',
            'acc5': pct(g['Accuracy']), 'bacc5': pct(g['Balanced accuracy']),
            'qwk5': k3(g['Quadratic weighted kappa']), 'kappa5': k3(g["Cohen's kappa"]),
            'mcc5': k3(g['MCC']), 'f1macro5': pct(g['F1 (macro)']), 'f1w5': pct(g['F1 (weighted)']),
            'precmacro5': pct(g['Precision (macro)']), 'recmacro5': pct(g['Recall (macro)']),
            'within1': pct(g['Within-one-grade accuracy']), 'top2': pct(g['Top-2 accuracy']),
            'logloss5': k3(g['Log loss']),
            'auc5': k3(g.get('ROC AUC (macro, OvR)', float('nan'))),
            'ap5': k3(g.get('Average precision (macro)', float('nan'))),
            'acc5ci': ci_pct(ci['acc5']), 'qwk5ci': ci_k3(ci['qwk5']), 'f1macro5ci': ci_pct(ci['f1macro5']),
            'refacc': pct(rf['Accuracy']), 'refsens': pct(rf['Sensitivity (recall)']),
            'refspec': pct(rf['Specificity']), 'refppv': pct(rf['Precision (PPV)']), 'refnpv': pct(rf['NPV']),
            'reff1': pct(rf['F1']), 'refauc': k3(rf['ROC AUC']), 'refthr': k3(rf['Threshold (from OOF)']),
            'refaccci': ci_pct(ci['ref_acc']), 'refsensci': ci_pct(ci['ref_sens']),
            'refspecci': ci_pct(ci['ref_spec']), 'refaucci': ci_k3(ci['ref_auc']),
            'rule': full['decision_rule'],
            'thr': ', '.join(f'{t:.2f}' for t in full['thresholds']),
            'oofacc': pct(full['oof']['acc5']), 'oofqwk': k3(full['oof']['qwk5']),
            'oofrefauc': k3(full['oof']['ref_auc']),
            'epochsrun': ', '.join(str(e) for e in full['epochs_run']),
        })
        fa, fq = full['oof']['fold_acc'], full['oof']['fold_qwk']
        mean = lambda v: sum(v) / len(v)
        std = lambda v: (sum((x - mean(v)) ** 2 for x in v) / len(v)) ** 0.5
        out['foldacc'] = f'{100 * mean(fa):.2f} $\\pm$ {100 * std(fa):.2f}'
        out['foldqwk'] = f'{mean(fq):.3f} $\\pm$ {std(fq):.3f}'
        for c in range(5):
            out[f'nid{c}'] = full['idrid_counts'][c]
            out[f'nte{c}'] = full['test_counts'][c]
            if 'aptos_counts' in full:
                out[f'nap{c}'] = full['aptos_counts'][c]
            out[f'p{c}'] = pct(full['per_class']['precision'][c])
            out[f'r{c}'] = pct(full['per_class']['recall'][c])
            out[f'f{c}'] = pct(full['per_class']['f1'][c])
            for d in range(5):
                out[f'cm{c}{d}'] = full['confusion5'][c][d]
        (tn, fp), (fn, tp) = full['confusion2']
        out.update({'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp})
        for name, key in RULE_KEYS.items():
            out[f'oof{key}'] = pct(full['oof_rules'][name])
            out[f'test{key}'] = pct(full['test_rules'][name])
            out[f'test{key}qwk'] = k3(full['test_rules_qwk'][name])
        ia = full['inference_ablation']
        out.update({
            'singleacc': f"{100 * ia['single_fold_acc_mean']:.2f} $\\pm$ {100 * ia['single_fold_acc_std']:.2f}",
            'singleqwk': f"{ia['single_fold_qwk_mean']:.3f} $\\pm$ {ia['single_fold_qwk_std']:.3f}",
            'notaacc': pct(ia['ensemble_noTTA_acc']), 'notaqwk': k3(ia['ensemble_noTTA_qwk']),
            'ttaacc': pct(ia['ensemble_TTA_acc']), 'ttaqwk': k3(ia['ensemble_TTA_qwk']),
        })

    for tag in ['full'] + ABLATION_TAGS:
        r = runs.get(tag)
        if not r:
            continue
        g, rf = r['grading'], r['referable']
        out[f'ab{tag}acc'] = pct(g['Accuracy'])
        out[f'ab{tag}qwk'] = k3(g['Quadratic weighted kappa'])
        out[f'ab{tag}f1'] = pct(g['F1 (macro)'])
        out[f'ab{tag}refauc'] = k3(rf['ROC AUC'])
        out[f'ab{tag}refsens'] = pct(rf['Sensitivity (recall)'])
        out[f'ab{tag}refspec'] = pct(rf['Specificity'])
        out[f'ab{tag}params'] = f"{r['params_M']:.2f}"
        if full and tag != 'full':
            if r['test_idx'] != full['test_idx']:
                raise SystemExit(f'results_{tag}.json uses a different test split from results_full.json')
            p, _, _ = mcnemar_exact(full['y_test'], full['pred_test'], r['pred_test'])
            out[f'ab{tag}p'] = fmt_p(p)

    lines = ['% Generated by fill_results.py -- do not edit by hand.']
    for k, v in sorted(out.items()):
        v = str(v).replace('%', '\\%').replace('_', '\\_')
        lines.append(f'\\expandafter\\def\\csname res@{k}\\endcsname{{{v}}}')
    with open(os.path.join(HERE, 'results.tex'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(f'results.tex written with {len(out)} values from runs: {sorted(runs)}')


if __name__ == '__main__':
    main()
