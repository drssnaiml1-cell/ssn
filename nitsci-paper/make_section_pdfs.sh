#!/usr/bin/env bash
# Builds the full paper, then writes one PDF per section into section_pdfs/,
# using the page ranges recorded in nitsci_paper.aux (cross-references stay intact).
set -euo pipefail
cd "$(dirname "$0")"
python3 fill_results.py
pdflatex -interaction=nonstopmode nitsci_paper >/dev/null
bibtex nitsci_paper >/dev/null
pdflatex -interaction=nonstopmode nitsci_paper >/dev/null
pdflatex -interaction=nonstopmode nitsci_paper >/dev/null
mkdir -p section_pdfs
python3 - <<'PY'
import re, subprocess
aux = open('nitsci_paper.aux').read()
starts = [int(p) for p in re.findall(r'\\contentsline \{section\}\{\\numberline \{\d\}[^}]*\}\{(\d+)\}', aux)]
names = ['01_introduction', '02_related_work', '03_materials', '04_method',
         '05_experimental_setup', '06_results', '07_discussion', '08_conclusion']
def label_page(name):
    return int(re.search(r'\\newlabel\{' + name + r'\}\{\{[^}]*\}\{(\d+)\}', aux).group(1))
total = int(subprocess.check_output(['pdfinfo', 'nitsci_paper.pdf'], text=True).split('Pages:')[1].split()[0])
decl, supp = label_page('start:decl'), label_page('start:supp')
names += ['09_declarations_references', '10_supplementary']
bounds = starts + [decl, supp, total + 1]
subprocess.run(['pdfseparate', '-f', '1', '-l', str(starts[0] - 1), 'nitsci_paper.pdf', 'section_pdfs/_p%d.pdf'], check=True, stderr=subprocess.DEVNULL)
front = [f'section_pdfs/_p{i}.pdf' for i in range(1, starts[0])]
subprocess.run(['pdfunite', *front, 'section_pdfs/00_title_abstract.pdf'] if len(front) > 1 else ['cp', front[0], 'section_pdfs/00_title_abstract.pdf'], check=True, stderr=subprocess.DEVNULL)
for n, a, b in zip(names, bounds, bounds[1:]):
    last = b - 1
    subprocess.run(['pdfseparate', '-f', str(a), '-l', str(last), 'nitsci_paper.pdf', 'section_pdfs/_p%d.pdf'], check=True, stderr=subprocess.DEVNULL)
    pages = [f'section_pdfs/_p{i}.pdf' for i in range(a, last + 1)]
    subprocess.run(['pdfunite', *pages, f'section_pdfs/{n}.pdf'] if len(pages) > 1 else ['cp', pages[0], f'section_pdfs/{n}.pdf'], check=True, stderr=subprocess.DEVNULL)
    print(f'{n}.pdf  pages {a}-{last}  ({last - a + 1} pages)')
import glob, os
for f in glob.glob('section_pdfs/_p*.pdf'):
    os.remove(f)
PY
