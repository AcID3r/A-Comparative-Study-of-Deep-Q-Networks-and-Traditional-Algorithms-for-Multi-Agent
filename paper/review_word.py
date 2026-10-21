"""Rasterize and check the independent preview or an actual native Word export."""
import argparse
import json
from pathlib import Path
import pdfplumber
import pypdfium2 as pdfium
from evaluation.final_protocol import digest
from evaluation.team_protocol import ROOT


def review(native=False):
    root=ROOT/'paper'; source=root/'Graph_Search_Research_Paper.docx'
    name='Graph_Search_Research_Paper.pdf' if native else 'Graph_Search_Research_Paper_preview.pdf'
    proof=json.loads((root/('word_native_render.json' if native else 'word_preview_provenance.json')).read_text())
    assert proof['source_sha256']==digest(source)
    if native: assert proof['native_render_complete'],'A real Word export is required'
    path=root/name; assert proof['pdf_sha256']==digest(path)
    pages=[]; all_text=[]
    with pdfplumber.open(path) as pdf:
        for i,page in enumerate(pdf.pages,1):
            text=page.extract_text() or ''; assert len(text)>20,(i,'empty page')
            outside=[c for c in page.chars if c['x0']<-.5 or c['x1']>page.width+.5 or c['top']<-.5 or c['bottom']>page.height+.5]
            assert not outside,(i,'out-of-page text')
            assert all(im['x0']>=-.5 and im['x1']<=page.width+.5 and im['top']>=-.5 and im['bottom']<=page.height+.5 for im in page.images),(i,'out-of-page image')
            all_text.append(text); pages.append(dict(page=i,characters=len(page.chars),images=len(page.images)))
    text='\n'.join(all_text)
    for title in ('Introduction','Related Work','Problem Formulation','Methodology',
                  'Experimental Setup','Results','Discussion','Limitations','Conclusion','References'):
        assert title in text,title
    for rate in ('89.17%','24.17%','22.19%'): assert rate in text
    destination=root/('word_native_pages' if native else 'word_preview_pages')/digest(path)[:12]
    destination.mkdir(parents=True,exist_ok=True)
    pdf=pdfium.PdfDocument(str(path))
    for i in range(len(pdf)):
        page=pdf[i]; bitmap=page.render(scale=1.4); bitmap.to_pil().save(destination/f'page_{i+1:02d}.png')
        bitmap.close(); page.close()
    pdf.close()
    (destination/'text.txt').write_text(text,encoding='utf-8')
    result=dict(docx_sha256=digest(source),pdf_sha256=digest(path),pages=pages,page_count=len(pages),
        text_outside_page=0,images_outside_page=0,required_sections_and_main_rates_present=True,native_word_render=native,
        review_directory=destination.relative_to(ROOT).as_posix(),
        visual_review='pending inspection',review_kind='Native Word export' if native else 'Independent preview only')
    (ROOT/'results/validation'/('CP-09-native-pages.json' if native else 'CP-09-preview-pages.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2)); return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--native',action='store_true')
    args=parser.parse_args(); review(args.native)
