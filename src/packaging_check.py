"""Internal check for the standalone build, including its document worker."""
import json
import tempfile
import threading
import zipfile
from pathlib import Path

def run(index_class,report):
    report=Path(report).resolve()
    report.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=report.parent) as temp:
        folder=Path(temp); docs=folder/'docs'; docs.mkdir()
        (docs/'Faculty notes.txt').write_text('searchable orchid phrase',encoding='utf8')
        with zipfile.ZipFile(docs/'Faculty List.xlsx','w') as z:
            z.writestr('xl/sharedStrings.xml','<root><t>hidden pineapple document</t></root>')
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
        writer=PdfWriter(); page=writer.add_blank_page(300,300)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
        stream=DecodedStreamObject(); stream.set_data(b'BT /F1 12 Tf 20 200 Td (marigold verification) Tj ET')
        page[NameObject('/Contents')]=writer._add_object(stream)
        with (docs/'report.pdf').open('wb') as f: writer.write(f)
        index=index_class(folder/'test.db'); index.add(str(docs))
        index.scan(threading.Event(),lambda s:None)
        assert len(index.search('faculty',ext='xlsx'))==1
        assert len(index.search('orchid','Contents'))==1
        assert len(index.search('pineapple','Contents'))==1
        assert len(index.search('marigold','Contents'))==1
        import tkinter as tk
        from filefinder_ui import App
        root=tk.Tk(); root.withdraw()
        app=App(root,index); root.update()
        assert app.logo.width()==256
        app.close()
    report.write_text(json.dumps({'passed':True,'checks':['standalone runtime','SQLite FTS','filename search','Office extraction','PDF extraction','multiprocessing worker','Tkinter UI','custom icon']}),encoding='utf8')

