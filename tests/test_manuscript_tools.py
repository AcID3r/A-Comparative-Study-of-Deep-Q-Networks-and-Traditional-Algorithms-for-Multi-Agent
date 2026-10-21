import tempfile
import unittest
from pathlib import Path
from paper.build_manuscript import to_latex
from paper.render_manuscript import render
import pdfplumber


class ManuscriptToolsTests(unittest.TestCase):
    def test_latex_preserves_equations_and_escapes_measured_percent(self):
        result=to_latex('# Title\n\n## Results\nA rate of 25.00% and [source](https://example.org).\n$$y=r+\\gamma Q$$\n| Method | Rate |\n|---|---|\n| shared | 25.00% |\n')
        self.assertIn(r'25.00\%',result)
        self.assertIn(r'\[y=r+\gamma Q\]',result)
        self.assertIn(r'\begin{longtable}',result)
        self.assertIn(r'\href{https://example.org}{source}',result)

    def test_pdf_real_table_wrap_and_equation_render(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary); source=directory/'test.md'
            source.write_text('# Scientific manuscript\n\n## Results\nA measured rate of 25.00%.\n\n**Table 1. Policy minus A* paths and L*.**\n\n| Method | Successful episodes |\n|---|---|\n| shared | 1 / 4 |\n\n$$y=r+\\gamma Q$$\n',encoding='utf-8')
            pdf=render(source,directory/'test.pdf')
            with pdfplumber.open(pdf) as document:
                text=''.join(p.extract_text() or '' for p in document.pages)
                self.assertIn('25.00%',text); self.assertIn('shared',text)
                self.assertIn('Policy minus A* paths and L*.',text)
                self.assertNotIn('**',text)
                self.assertTrue(all(c['x0']>=0 and c['x1']<=p.width+.5 for p in document.pages for c in p.chars))
            self.assertTrue((directory/'equations/equation_1.png').exists())


if __name__=='__main__': unittest.main()
