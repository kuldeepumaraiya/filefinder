import sys, threading, tempfile, time, zipfile, os, shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import filefinder as ff
import tkinter as tk

def pump(root,seconds=.8):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        root.update(); time.sleep(.01)

def main():
    (Path(__file__).resolve().parents[1]/'build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'build') as tmp:
        base=Path(tmp).resolve(); docs=base/'docs'; docs.mkdir()
        (docs/'नमस्ते दुनिया.txt').write_text('hello Unicode',encoding='utf8')
        (docs/'Faculty List. Data.xlsx').write_bytes(b'bad workbook')
        (docs/'~$office.docx').write_bytes(b'lock file')
        word=docs/'Formatted.docx'
        with zipfile.ZipFile(word,'w') as z:
            z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>fac</w:t></w:r><w:r><w:t>ulty list</w:t></w:r></w:p></w:body></w:document>')
        longdir=docs/('deep_directory_name/'*12)
        os.makedirs(ff.io_path(longdir))
        with open(ff.io_path(longdir/'long_path_test.txt'),'w') as f: f.write('longpath searchable')
        index=ff.Index(base/'test.db'); index.add(str(docs))
        index.scan(threading.Event(),lambda s:None)
        assert index.search('नमस्ते दुनिया','Filename')
        assert index.search('faculty','Contents')[0]['name']=='Formatted.docx'
        assert len(index.search('','Everywhere','xlsx,docx'))==3
        assert index.search('longpath','Contents')
        assert index.detail(index.search('~$office','Filename')[0]['id'])['status'].startswith('Name only: temporary')
        try: index.add(str(base/'absent'))
        except ValueError: pass
        else: raise AssertionError('Missing folder accepted')
        root=tk.Tk(); app=ff.App(root,index)
        errors=[]; root.report_callback_exception=lambda *args:errors.append(args)
        app.query.set('faculty'); pump(root)
        assert len(app.rows)==2
        app.category('Spreadsheets'); pump(root)
        assert len(app.rows)==1 and next(iter(app.rows.values()))['ext']=='.xlsx'
        app.category('All files'); app.query.set('faculty'); pump(root)
        app.sort('name'); pump(root)
        assert [app.rows[k]['name'] for k in app.tree.get_children()]==sorted(r['name'] for r in app.rows.values())
        for geometry in ['1320x820','1040x650']:
            root.geometry(geometry); pump(root,.25)
            for widget in (app.openbtn,app.revealbtn,app.copybtn,app.addbtn,app.scanbtn):
                assert widget.winfo_ismapped(), str(widget)
                y=widget.winfo_rooty()-root.winfo_rooty()
                assert y+widget.winfo_height()<=root.winfo_height(), (geometry,str(widget),y,root.winfo_height())
        app.query.set('unfindable67890'); pump(root)
        assert not app.tree.get_children() and not app.text.get('1.0','end').strip()
        assert str(app.openbtn['state'])=='disabled'
        assert app.empty.winfo_ismapped()
        app.query.set('long_path'); app.ext.set('txt'); pump(root)
        assert len(app.rows)==1
        app.copy(); assert root.clipboard_get().endswith('long_path_test.txt')
        app.scan(); pump(root,1)
        assert not app.is_scanning()
        assert str(app.scanbtn['state'])=='normal'
        assert not errors,errors
        app.close()
        # Remove the entire deep branch with the Windows extended path prefix;
        # the default TemporaryDirectory cleanup cannot traverse long paths.
        deep_root=docs/'deep_directory_name'
        assert os.path.commonpath([str(base),str(deep_root)])==str(base)
        shutil.rmtree(ff.io_path(deep_root))
        print('PASS: Unicode filenames, Word formatting runs, long Windows paths, Office lock files, multi-type filters, live search, sorting, action visibility at 1040x650/1320x820, empty state, clipboard, refresh, clean close')

if __name__=='__main__': main()
