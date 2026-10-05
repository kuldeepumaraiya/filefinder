import sys, tempfile, threading, zipfile, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from filefinder import Index, App, extract
import tkinter as tk

def main():
    (Path(__file__).resolve().parents[1]/'build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'build') as tmp:
        base=Path(tmp).resolve(); docs=base/'docs'; docs.mkdir()
        (docs/'Budget 2026.txt').write_text('The orchid project has an annual budget of forty rupees.',encoding='utf8')
        (docs/'photo.jpg').write_bytes(b'image')
        (docs/'unicode.txt').write_text('नमस्ते दुनिया café',encoding='utf8')
        for ext,part in [('docx','word/document.xml'),('pptx','ppt/slides/slide1.xml'),('xlsx','xl/sharedStrings.xml')]:
            with zipfile.ZipFile(docs/('office.'+ext),'w') as z:
                z.writestr(part,'<root><t>hidden pineapple document</t></root>')
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
        writer=PdfWriter(); page=writer.add_blank_page(300,300)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
        stream=DecodedStreamObject(); stream.set_data(b'BT /F1 12 Tf 20 200 Td (secret marigold report) Tj ET')
        page[NameObject('/Contents')]=writer._add_object(stream)
        with open(docs/'report.pdf','wb') as f: writer.write(f)
        index=Index(base/'index.db'); index.add(str(docs))
        statuses=[]; index.scan(threading.Event(),statuses.append)
        assert len(index.search('budget','Filename'))==1
        assert len(index.search('orchid','Contents'))==1
        assert len(index.search('"annual budget"','Contents'))==1
        assert len(index.search('pineapple','Contents'))==3
        assert len(index.search('pineapple','Contents','docx'))==1
        assert len(index.search('marigold','Contents'))==1
        assert len(index.search('नमस्ते','Contents'))==1
        assert len(index.search('photo','Filename'))==1
        assert index.search('%','Filename')==[]
        assert index.search('" *','Contents')==[]
        try: index.add(str(docs/'sub'))
        except ValueError: pass
        else: raise AssertionError('Overlap accepted')
        index.scan(threading.Event(),statuses.append)
        assert len(index.search('orchid','Contents'))==1
        (docs/'Budget 2026.txt').write_text('replacement sunflower',encoding='utf8')
        (docs/'photo.jpg').unlink()
        index.scan(threading.Event(),statuses.append)
        assert not index.search('orchid','Contents')
        assert index.search('sunflower','Contents')
        assert not index.search('photo','Filename')
        root=tk.Tk(); app=App(root,index); root.update()
        app.query.set('marigold'); app.search()
        for _ in range(20): root.update(); time.sleep(.05)
        assert len(app.tree.get_children())==1
        app.preview()
        for _ in range(20): root.update(); time.sleep(.05)
        assert 'marigold' in app.text.get('1.0','end')
        root.destroy()
        index.remove(str(docs)); assert not index.search('marigold')
        assert (docs/'report.pdf').exists()
        print('PASS: filenames, text, phrase, Unicode, PDF, Office, filters, overlap, incremental updates, deletion, GUI search/preview, non-destructive removal')

if __name__ == '__main__': main()
