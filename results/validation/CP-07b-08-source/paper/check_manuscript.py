"""Trace CP-08 claims to outputs; inspect PDF text/bounds and render review pages."""
import argparse
import json
import re
from pathlib import Path
import pdfplumber
import pypdfium2 as pdfium
from evaluation.final_protocol import digest
from evaluation.team_protocol import ROOT


def check(analysis):
    analysis=Path(analysis).resolve(); root=ROOT/'paper'
    report=json.loads((analysis/'report.json').read_text())
    claims=json.loads((root/'claims.json').read_text())
    provenance=json.loads((root/'manuscript_provenance.json').read_text())
    for path,value in provenance['input_sha256'].items(): assert digest(ROOT/path)==value,path
    assert digest(root/'paper.md')==provenance['manuscript_sha256']
    assert digest(root/'paper.tex')==provenance['latex_sha256']
    assert digest(root/'claims.json')==provenance['claims_sha256']
    assert provenance['qenn_sha256']==digest(ROOT/'QENN_Research_Paper_Madhav_Joshi (1).docx')=='0eb7c34b6358da752b52c38fd9af9daead8469c2df2216df1c272f07c47392f8'
    overall={g['method']:g for g in report['groups']['overall']}
    for method,values in claims['overall'].items():
        for name,value in values.items(): assert overall[method][name]==value
    for name in ('unique_episodes','fresh_timing_rollouts','audit'): assert claims[name]==report[name]
    for name in ('h1','h2','h3','h4'): assert claims[name]==report['contrasts'][name]
    markdown=(root/'paper.md').read_text(encoding='utf-8')
    for n,title in enumerate(('Introduction','Related Work','Problem Formulation','Methodology','Experimental Setup','Results','Discussion','Limitations','Conclusion'),1):
        assert f'## {n}. {title}' in markdown
    assert '## Abstract' in markdown and '## References' in markdown
    assert not re.search(r'\bTODO\b|\bTBD\b|\[insert|\[result\]|placeholder',markdown,re.IGNORECASE)
    references=json.loads((root/'references.json').read_text())
    body=markdown.split('## References')[0]
    assert {int(x) for x in re.findall(r'\[(\d+)\]',body)}=={r['id'] for r in references}
    for reference in references:
        assert reference['verified_on']=='2026-10-07' and reference['primary_evidence'].startswith('https://')
    for name in ('overall','condition_agents','size_condition','h1_paired','h2_exposed','h4_paired','training','runtime','static_single_gap'):
        assert (analysis/'tables'/f'{name}.md').read_text().strip() in markdown
    images=re.findall(r'!\[([^]]*)\]\(([^)]+)\)',markdown)
    assert len(images)==7
    for _,path in images: assert (root/path).is_file()
    pdf=root/'paper.pdf'; bounds_issues=[]; page_data=[]; full_text=[]
    with pdfplumber.open(pdf) as document:
        for i,page in enumerate(document.pages,1):
            text=page.extract_text() or ''; full_text.append(text)
            assert len(text)>20,(i,'empty page')
            for char in page.chars:
                if char['x0']<0 or char['x1']>page.width+.5 or char['top']<0 or char['bottom']>page.height+.5:
                    bounds_issues.append(dict(page=i,char=char['text'],bbox=[char['x0'],char['top'],char['x1'],char['bottom']]))
            page_data.append(dict(page=i,characters=len(page.chars),images=len(page.images),width=page.width,height=page.height))
    assert not bounds_issues,bounds_issues[:5]
    text='\n'.join(full_text)
    for name in ('Abstract','Introduction','Related Work','Problem Formulation','Methodology','Experimental Setup','Results','Discussion','Limitations','Conclusion','References'):
        assert name in text,name
    for values in claims['overall'].values(): assert f'{100*values["success_rate"]:.2f}%' in text
    review=root/'review_pages'; review.mkdir(exist_ok=True)
    document=pdfium.PdfDocument(str(pdf))
    for i in range(len(document)):
        page=document[i]; bitmap=page.render(scale=1.3); bitmap.to_pil().save(review/f'page_{i+1:02d}.png')
        bitmap.close(); page.close()
    document.close()
    proof=dict(manuscript_sha256=digest(root/'paper.md'),pdf_sha256=digest(pdf),
        latex_source_sha256=digest(root/'paper.tex'),latex_compilation='not run: no local TeX engine; PDF rendered with ReportLab',
        analysis_sha256=digest(analysis/'report.json'),references=9,figure_count=7,
        numeric_claims_and_tables_match=True,required_sections_present=True,qenn_unchanged=True,
        page_count=len(page_data),pages=page_data,text_outside_page=0,
        rendered_review_pages=len(page_data),visual_review='pending human/agent inspection',
        review_dependencies={'pdfplumber':'0.11.10','pypdfium2':'5.10.1'},
        author_metadata=json.loads((root/'author.json').read_text()))
    (ROOT/'results/validation/CP-08-checks.json').write_text(json.dumps(proof,indent=2)+'\n')
    (root/'pdf_text.txt').write_text(text,encoding='utf-8')
    print(json.dumps(proof,indent=2))
    return proof


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('analysis',type=Path)
    args=parser.parse_args(); check(args.analysis)


if __name__=='__main__': main()
