# NITSCI: research paper from `NITSCI_v2_high_accuracy.ipynb`

| File | Purpose |
|------|---------|
| `nitsci_paper_combined.tex` / `.pdf` | **Complete paper in one file**: all sections inline, continuous layout, bibliography embedded; compiles with `pdflatex` alone (needs only `figures/`). Regenerate with `python make_combined.py` |
| `nitsci_paper.tex` / `.pdf` | Full manuscript (title, abstract, declarations; inputs the section files) |
| `sections/01_introduction.tex` … `08_conclusion.tex` | One file per section, each about 2 pages (Method and Results about 2.5–3, because of the architecture diagram and the results tables) |
| `sections/09_supplementary.tex` | Supplementary figures (grade histograms, training curves) |
| `figures/nitsci_method.pdf` (+ `.png`) | Method overview figure (Fig. 2), HEL-Net style. Rebuild with `python figures/method_figure/make_method_figure.py`; add `--fundus img1.jpg img2.jpg ...` to use real IDRiD/APTOS photographs instead of the synthetic ones |
| `section_pdfs/` | A separate PDF for each section, cut from the full paper |
| `make_section_pdfs.sh` | Rebuilds the paper and the per-section PDFs |
| `refs.bib` | 80 references (all cited), each a real publication with DOI/venue |
| `export_results_cell.py` | Paste as the last notebook cell: exports every number plus the figures |
| `ablation_variants.py` | Drop-in model variants for the architecture ablations |
| `fill_results.py` | Turns `results_*.json` into `results.tex` (adds McNemar tests between runs) |

## Why the PDF shows red markers

The notebook (`NITSCI_v2_high_accuracy.ipynb`, included here) has **no saved outputs**, so the manuscript contains no
invented numbers. Each experimental value is a slot such as **[acc5]**, filled
from your own runs. Red *[AUTHOR: ...]* notes mark sentences whose wording depends
on the results (for example, which ablation mattered).

Numbers that were measured directly from the code (CPU, random weights):
21.25 M parameters (19.85 M backbone + 1.40 M head), 23.0 GFLOPs at 448 px,
19.92 M for the plain baseline, and 196 tokens of width 256.

## How to fill the paper (Colab, T4 GPU)

1. Run the notebook as is, paste `export_results_cell.py` as the last cell, and run it
   with `RUN_TAG = 'full'`. Download `results_full.json` and the `figures/` folder.
2. Ablations: run each one in a fresh runtime, and export it with the matching `RUN_TAG`.
   * `noaptos`: set `USE_APTOS = False`
   * `clahe`: set `PREPROC = 'clahe'` and delete `aptos_pretrained.pth`
   * `noreg`: set `REG_WEIGHT = 0.0`
   * `plain`, `nolesion`, `nocross`, `nogate`: paste `ablation_variants.py` after the
     model cell, set `VARIANT`, and delete `aptos_pretrained.pth`
3. Copy all `results_*.json` files and `figures/` here, then build:
   ```
   ./make_section_pdfs.sh        # fills results, builds the paper and section_pdfs/
   python make_combined.py       # single-file version: nitsci_paper_combined.tex
   pdflatex nitsci_paper_combined && pdflatex nitsci_paper_combined
   ```
   For journal submission, set `\sectionsonnewpagesfalse` in `nitsci_paper.tex` so that
   sections no longer start on new pages.
4. Replace every red *[AUTHOR: ...]* note with text that matches your numbers, then
   search the PDF for `[` to confirm that no red slot remains.

## Acceptance readiness (honest estimate)

There is no formula for acceptance. The estimates below are a judgement based on
what Q1/Q2 medical-imaging reviewers typically ask for.

| State of the paper | Likely outcome at a Q1 journal (e.g. CBM, BSPC, IVC) |
|---|---|
| As it stands, with only the `full` run | ~10-20%: desk reject or major revision. A single dataset, a random 15% split and no baselines are the usual reasons. |
| With all ablations filled and the [AUTHOR] notes written | ~30-40% |
| Also using the **official IDRiD split** and comparing with the challenge (Porwal et al., 2020) | ~45-55% |
| Also with **external validation** (Messidor-2 / DDR), 3 seeds and released code | ~55-65% at a Q1/Q2 venue; higher at Q2/Q3 journals |

The five changes that would raise acceptance odds most:
1. Evaluate on the official IDRiD grading test split (103 images), so the results
   can be compared with published work.
2. Test on at least one external dataset without retraining.
3. Repeat the full run with 3 seeds and report mean ± SD.
4. Check the lesion-attention maps against the IDRiD lesion masks (for example
   with a pointing-game metric). Without this, do not claim that the model
   localises lesions.
5. Release code and weights (GitHub + Zenodo DOI).
