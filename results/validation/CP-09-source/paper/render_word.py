"""Export the new DOCX with native Word; record an honest unavailable status."""
import argparse
import json
from pathlib import Path
from evaluation.final_protocol import digest
from evaluation.team_protocol import ROOT


def render(source,output):
    source,output=Path(source).resolve(),Path(output).resolve()
    if source==ROOT/'QENN_Research_Paper_Madhav_Joshi (1).docx':
        raise ValueError('Use the new manuscript, not the reference')
    before=digest(source); app=None; document=None
    result=dict(source_sha256=before,engine='Microsoft Word COM',native_render_complete=False)
    try:
        import win32com.client
        app=win32com.client.DispatchEx('Word.Application')
        app.Visible=False; app.DisplayAlerts=0
        document=app.Documents.Open(str(source),ReadOnly=True,AddToRecentFiles=False,Visible=False)
        document.Repaginate()
        document.ExportAsFixedFormat(OutputFileName=str(output),ExportFormat=17,OpenAfterExport=False)
        result.update(native_render_complete=True,word_version=app.Version,
                      pages=int(document.ComputeStatistics(2)),pdf_sha256=digest(output))
    except Exception as error:
        result.update(error_type=type(error).__name__,error=str(error),
                      status='Native pagination unresolved; DOCX structural checks and independent preview are separate.')
    finally:
        if document is not None: document.Close(False)
        if app is not None: app.Quit()
    assert digest(source)==before,'Exporter must not save changes to DOCX'
    (source.parent/'word_native_render.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path,nargs='?',default=ROOT/'paper/Graph_Search_Research_Paper.docx')
    parser.add_argument('--output',type=Path,default=ROOT/'paper/Graph_Search_Research_Paper.pdf')
    args=parser.parse_args(); result=render(args.source,args.output)
    raise SystemExit(0 if result['native_render_complete'] else 2)
