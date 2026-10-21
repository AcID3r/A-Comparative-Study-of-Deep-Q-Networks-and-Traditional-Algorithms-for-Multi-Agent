"""Independent DOCX-content preview; this is not a native Word layout renderer."""
import argparse
import html
import json
from io import BytesIO
from pathlib import Path
from docx import Document
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph
from docx.oxml.ns import qn
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Table,TableStyle,Image,KeepTogether,Spacer,NextPageTemplate
from evaluation.final_protocol import digest
from evaluation.team_protocol import ROOT


def rich(paragraph):
    parts=[]
    for element in paragraph._p:
        runs=[element] if element.tag==qn('w:r') else list(element.findall(qn('w:r')))
        for run in runs:
            text=html.escape(''.join(t.text or '' for t in run.findall(qn('w:t'))))
            props=run.find(qn('w:rPr'))
            if props is not None:
                if props.find(qn('w:b')) is not None and props.find(qn('w:b')).get(qn('w:val'),'1')!='0': text='<b>'+text+'</b>'
                if props.find(qn('w:i')) is not None and props.find(qn('w:i')).get(qn('w:val'),'1')!='0': text='<i>'+text+'</i>'
            parts.append(text)
    return ''.join(parts)


def render(source,output):
    source,output=Path(source).resolve(),Path(output).resolve(); document=Document(source)
    before=digest(source); section=document.sections[0]
    width,height=section.page_width.pt,section.page_height.pt
    left,right,top,bottom=[getattr(section,n).pt for n in ('left_margin','right_margin','top_margin','bottom_margin')]
    full=width-left-right; gap=22; column=(full-gap)/2
    font='Times-Roman'
    fonts=Path('C:/Windows/Fonts')
    if (fonts/'times.ttf').exists():
        for name,file in [('PreviewTimes','times.ttf'),('PreviewTimesBold','timesbd.ttf'),('PreviewTimesItalic','timesi.ttf')]:
            pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
        font='PreviewTimes'; pdfmetrics.registerFontFamily(font,normal=font,bold='PreviewTimesBold',italic='PreviewTimesItalic',boldItalic='PreviewTimesBold')
    normal=ParagraphStyle('Body',fontName=font,fontSize=11,leading=13.2,spaceAfter=4,alignment=4,firstLineIndent=18)
    cell_style=ParagraphStyle('Cell',parent=normal,fontSize=8,leading=9,spaceAfter=0,firstLineIndent=0,alignment=0)
    def formatted(p):
        size=next((r.font.size.pt for r in p.runs if r.font.size is not None),11)
        align={0:0,1:1,2:2,3:4,None:0}.get(p.alignment,0)
        style=ParagraphStyle('P',parent=normal,fontSize=size,leading=size*1.2,alignment=align,
            spaceBefore=p.paragraph_format.space_before.pt if p.paragraph_format.space_before else 0,
            spaceAfter=p.paragraph_format.space_after.pt if p.paragraph_format.space_after else 4,
            firstLineIndent=p.paragraph_format.first_line_indent.pt if p.paragraph_format.first_line_indent else 0,
            keepWithNext=bool(p.paragraph_format.keep_with_next))
        return Paragraph(rich(p),style)
    opening=[]; story=[]; opened=False; equations=0; blocks=0
    for element in document.element.body:
        if element.tag==qn('w:p'):
            p=DocxParagraph(element,document)
            if not opened:
                if p.text.strip(): opening.append(formatted(p))
                if p.text.startswith('Index Terms—'): opened=True
                continue
            drawings=element.xpath('.//a:blip')
            if drawings:
                relationship=document.part.related_parts[drawings[0].get(qn('r:embed'))]
                image=Image(BytesIO(relationship.blob)); image.drawWidth=3.3*72
                image.drawHeight=image.imageHeight*image.drawWidth/image.imageWidth
                image.keepWithNext=True
                story.append(image); blocks+=1; continue
            if element.findall('.//'+qn('m:oMath')):
                equations+=1
                image=Image(str(ROOT/f'paper/equations/equation_{equations}.png'))
                natural_width,natural_height=image.imageWidth,image.imageHeight
                image.drawWidth=column-40; image.drawHeight=natural_height*image.drawWidth/natural_width
                equation_table=Table([[image,Paragraph(f'({equations})',cell_style)]],colWidths=[column-20,20])
                equation_table.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),
                    ('RIGHTPADDING',(0,0),(-1,-1),0),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
                story.append(equation_table)
                blocks+=1; continue
            if p.text.strip(): story.append(formatted(p)); blocks+=1
        elif element.tag==qn('w:tbl'):
            table=DocxTable(element,document)
            data=[[Paragraph(html.escape(c.text.replace('\u200b','')),cell_style) for c in r.cells] for r in table.rows]
            widths=[c.width.pt for c in table.columns]
            display=Table(data,colWidths=widths,repeatRows=1)
            display.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.3,colors.grey),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8edf3')),
                ('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2),
                ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
            story.extend([display,Spacer(1,5)]); blocks+=1
    opening_height=sum(p.wrap(full,height)[1]+p.getSpaceBefore()+p.getSpaceAfter() for p in opening)+8
    first_height=height-top-bottom-opening_height
    if first_height<100: raise ValueError('Opening leaves insufficient preview space')
    def footer(canvas,doc):
        canvas.setFont(font,7)
        canvas.drawString(left,18,'Independent DOCX preview — native Word pagination unverified')
        canvas.drawRightString(width-right,18,str(doc.page))
    def first(canvas,doc):
        footer(canvas,doc); y=height-top
        for p in opening:
            y-=p.getSpaceBefore(); _,h=p.wrap(full,height); y-=h
            p.drawOn(canvas,left,y); y-=p.getSpaceAfter()
    frame=lambda x,h:Frame(x,bottom,column,h,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    pdf=BaseDocTemplate(str(output),pagesize=(width,height),title=document.core_properties.title,
                        author=document.core_properties.author)
    pdf.addPageTemplates([PageTemplate(id='First',frames=[frame(left,first_height),frame(left+column+gap,first_height)],onPage=first),
        PageTemplate(id='Body',frames=[frame(left,height-top-bottom),frame(left+column+gap,height-top-bottom)],onPage=footer)])
    pdf.build([NextPageTemplate('Body')]+story)
    assert digest(source)==before
    result=dict(source_sha256=before,pdf_sha256=digest(output),renderer='Independent DOCX XML/ReportLab preview',
        native_word_pagination_verified=False,body_blocks=blocks,opening_blocks=len(opening),equations=equations)
    (source.parent/'word_preview_provenance.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2)); return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'paper/Graph_Search_Research_Paper.docx')
    parser.add_argument('--output',type=Path,default=ROOT/'paper/Graph_Search_Research_Paper_preview.pdf')
    args=parser.parse_args(); render(args.source,args.output)
