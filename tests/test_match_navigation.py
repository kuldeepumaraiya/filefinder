import sys,time,tempfile,threading,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import tkinter as tk
from filefinder import Index,App
from file_previews import render_file

def pump(root,seconds=.7):
    end=time.monotonic()+seconds
    while time.monotonic()<end:root.update();time.sleep(.01)

def main():
    with tempfile.TemporaryDirectory() as tmp:
        base=Path(tmp);docs=base/'docs';docs.mkdir()
        content='Kuldeep first\n'+('unrelated line\n'*1600)+'Kuldeep middle\n'+('another line\n'*2000)+'KULDEEP last'
        (docs/'Faculty.txt').write_text(content,encoding='utf8')
        with zipfile.ZipFile(docs/'Faculty.docx','w') as z:
            z.writestr('word/document.xml','<root><t>'+content+'</t></root>')
        from PIL import Image
        Image.new('RGB',(600,400),'purple').save(docs/'logo.png')
        from pypdf import PdfWriter
        writer=PdfWriter();writer.add_blank_page(300,400);writer.add_blank_page(300,400)
        with (docs/'book.pdf').open('wb') as f:writer.write(f)
        index=Index(base/'index.db');index.add(str(docs));index.scan(threading.Event(),lambda s:None)
        root=tk.Tk();app=App(root,index);app.query.set('Kuldeep');app.ext.set('txt');pump(root)
        assert len(app.matches)==3,app.match_label.get()
        assert app.preview_content.replace('\r\n','\n')==content
        app.move_match(1);assert app.match_index==1
        assert app.text.get(*app.text.tag_ranges('active_hit'))=='Kuldeep'
        app.move_match(1);assert app.match_index==2
        assert app.text.get(*app.text.tag_ranges('active_hit'))=='KULDEEP'
        assert int(app.text.index(app.text.tag_ranges('active_hit')[0]).split('.')[0])>3000
        app.move_match(1);assert app.match_index==0
        app.move_match(-1);assert app.match_index==2
        app.find_query.set('"Kuldeep middle"');pump(root)
        assert len(app.matches)==1 and app.text.get(*app.text.tag_ranges('active_hit'))=='Kuldeep middle'
        app.find_query.set('zzzxq987654');pump(root)
        assert not app.matches and str(app.nextbtn['state'])=='disabled'
        app.query.set('Faculty');app.ext.set('docx');pump(root)
        app.find_query.set('kuldeep');pump(root)
        assert len(app.matches)==3
        pic,pages,error=render_file(docs/'logo.png',0,300,200)
        assert pic and pic.width<=300 and not error
        pic,pages,error=render_file(docs/'book.pdf',1,300,200)
        assert pic and pages==2 and not error,error
        app.query.set('book');app.ext.set('pdf');pump(root)
        app.preview_tabs.select(1);pump(root,1)
        assert app.visual_pages==2
        app.change_page(1);pump(root,.6);assert app.visual_page==1
        app.query.set('unfindable98765');pump(root)
        assert not app.matches and app.visual_row is None
        app.close()
    print('PASS: full-text DOCX/text matches past 14k characters, next/previous wrap, exact phrase, active hit, reset, image preview, PDF page preview/navigation')

if __name__=='__main__':main()
