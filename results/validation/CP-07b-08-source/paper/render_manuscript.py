"""Render reviewed Markdown as a readable scientific PDF, before CP-09 Word layout."""
import argparse
import html
import re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,KeepTogether


def inline(text):
    escaped=html.escape(text)
    escaped=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:f'<a href="{html.escape(m[2],quote=True)}" color="#254b87">{m[1]}</a>',escaped)
    escaped=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',escaped)
    return escaped.replace('`','')


def render(source,output):
    source,output=Path(source),Path(output)
    fonts=Path('C:/Windows/Fonts')
    body,bold,italic='Times-Roman','Times-Bold','Times-Italic'
    if all((fonts/p).exists() for p in ('times.ttf','timesbd.ttf','timesi.ttf')):
        for name,path in [('ResearchTimes','times.ttf'),('ResearchTimesBold','timesbd.ttf'),('ResearchTimesItalic','timesi.ttf')]:
            pdfmetrics.registerFont(TTFont(name,str(fonts/path)))
        body,bold,italic='ResearchTimes','ResearchTimesBold','ResearchTimesItalic'
        pdfmetrics.registerFontFamily(body,normal=body,bold=bold,italic=italic,boldItalic=bold)
    styles=getSampleStyleSheet()
    for name in ('Normal','Heading1','Heading2','Heading3','Title'):
        styles[name].fontName=bold if name!='Normal' else body
    styles['Normal'].fontSize=10; styles['Normal'].leading=13.5; styles['Normal'].spaceAfter=7
    styles['Title'].fontSize=17; styles['Title'].leading=21
    styles['Heading1'].fontSize=13; styles['Heading1'].leading=17
    styles['Heading2'].fontSize=11; styles['Heading2'].leading=14
    styles.add(ParagraphStyle('Caption',parent=styles['Normal'],fontName=italic,fontSize=9,leading=11,alignment=TA_CENTER))
    styles.add(ParagraphStyle('TableCell',parent=styles['Normal'],fontSize=7.4,leading=9,spaceAfter=0))
    styles.add(ParagraphStyle('TableCaption',parent=styles['Normal'],keepWithNext=True))
    width=174*mm; story=[]; lines=source.read_text(encoding='utf-8').splitlines(); i=0
    equation_directory=source.parent/'equations'; equation_directory.mkdir(exist_ok=True); equation_count=0
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1; continue
        if line.startswith('$$'):
            import os
            os.environ.setdefault('MPLCONFIGDIR',str(source.parent.parent/'.cache/matplotlib'))
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            formula=line.strip('$'); equation_count+=1
            fig=plt.figure(figsize=(7, .55)); fig.text(.5,.5,'$'+formula+'$',ha='center',va='center',fontsize=12)
            destination=equation_directory/f'equation_{equation_count}.png'
            fig.savefig(destination,dpi=200,bbox_inches='tight',pad_inches=.08); plt.close(fig)
            image=Image(str(destination)); image.drawWidth=min(width,image.imageWidth*.25); image.drawHeight=image.imageHeight*image.drawWidth/image.imageWidth
            story.extend([image,Spacer(1,5)]); i+=1; continue
        image_match=re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)',line)
        if image_match:
            path=source.parent/image_match[2]; image=Image(str(path))
            scale=min(width/image.imageWidth,95*mm/image.imageHeight)
            image.drawWidth=image.imageWidth*scale; image.drawHeight=image.imageHeight*scale
            story.append(KeepTogether([Spacer(1,5),image,Paragraph(inline(image_match[1]),styles['Caption']),Spacer(1,8)]))
            i+=1; continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                values=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+',v) for v in values): rows.append(values)
                i+=1
            columns=len(rows[0]); weights=[max(len(r[c]) for r in rows) for c in range(columns)]
            # Limit long headings' effect; let Paragraph wrap without spilling across columns.
            weights=[max(9,min(w,24)) for w in weights]; column_widths=[width*w/sum(weights) for w in weights]
            table=Table([[Paragraph(inline(v),styles['TableCell']) for v in r] for r in rows],colWidths=column_widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8edf3')),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#68798c')),
                ('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#68798c')),
                ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
                ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
            story.extend([table,Spacer(1,10)]); continue
        heading=re.match(r'^(#{1,4}) (.*)',line)
        if heading:
            depth=len(heading[1]); name='Title' if depth==1 else 'Heading1' if depth==2 else 'Heading2'
            story.append(Paragraph(inline(heading[2]),styles[name])); i+=1; continue
        paragraph=[line]; i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','![','$$')):
            paragraph.append(lines[i].strip()); i+=1
        story.append(Paragraph(inline(' '.join(paragraph)),styles['TableCaption'] if paragraph[0].startswith('**Table ') else styles['Normal']))
    def page_number(canvas,doc):
        canvas.saveState(); canvas.setFont(body,8)
        canvas.drawRightString(192*mm,12*mm,f'{doc.page}'); canvas.restoreState()
    document=SimpleDocTemplate(str(output),pagesize=(210*mm,297*mm),leftMargin=18*mm,rightMargin=18*mm,
        topMargin=17*mm,bottomMargin=19*mm,title=lines[0].lstrip('# '),author='Madhav Joshi')
    document.build(story,onFirstPage=page_number,onLaterPages=page_number)
    print(f'Rendered manuscript: {output}',flush=True)
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True); args=parser.parse_args(); render(args.source,args.output)


if __name__=='__main__': main()
