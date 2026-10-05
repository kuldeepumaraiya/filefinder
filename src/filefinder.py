"""FileFinder: private, persistent desktop filename and document search."""
from pathlib import Path
import os, sys, sqlite3, threading, queue, time, re, zipfile, subprocess, multiprocessing, logging
from contextlib import contextmanager
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BASE = Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'vendor'))
MAX_BYTES = 32 * 1024 * 1024
MAX_TEXT = 1_000_000
TEXT = set('.txt .md .csv .tsv .log .json .xml .html .htm .css .js .ts .tsx .jsx .py .java .c .cpp .h .cs .sql .yaml .yml .ini .cfg .toml .tex .rst .srt .vtt .eml .ps1 .bat .sh'.split())
SKIP = {'windows', 'program files', 'program files (x86)', 'programdata', 'appdata', '$recycle.bin', 'system volume information', '.git', 'node_modules', '__pycache__', '.venv', 'venv'}

def descend(path):
    try:
        return path.name.lower() not in SKIP and not os.path.islink(io_path(path)) and Path(os.path.realpath(io_path(path))) != Path(io_path(BASE)) and os.path.isdir(io_path(path))
    except OSError:
        return False

def io_path(path):
    """Allow the indexer to read Windows paths longer than MAX_PATH."""
    value = os.path.abspath(str(path))
    if os.name != 'nt' or value.startswith('\\\\?\\'): return value
    return '\\\\?\\UNC\\' + value[2:] if value.startswith('\\\\') else '\\\\?\\' + value

def extract(path):
    path = Path(io_path(path))
    ext = path.suffix.lower()
    if path.stat().st_size > MAX_BYTES:
        return '', 'Name only: exceeds 32 MB content limit'
    if ext in TEXT:
        data = path.read_bytes()
        encoding = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
        value = data.decode(encoding, errors='replace')
    elif ext in {'.docx', '.pptx', '.xlsx', '.odt', '.ods', '.odp'}:
        parts = []
        with zipfile.ZipFile(path) as z:
            total = 0
            for info in z.infolist():
                name = info.filename
                relevant = (name.startswith('word/') and name.endswith('.xml') and any(x in name for x in ['document', 'header', 'footer', 'footnotes', 'endnotes'])) or (name.startswith('ppt/slides/slide') and name.endswith('.xml')) or (name.startswith('xl/') and (name == 'xl/sharedStrings.xml' or name.startswith('xl/worksheets/sheet')) and name.endswith('.xml')) or name == 'content.xml'
                if not relevant:
                    continue
                total += info.file_size
                if total > 64 * 1024 * 1024:
                    return '\n'.join(parts)[:MAX_TEXT], 'Partial: expanded document limit'
                root = ET.fromstring(z.read(info))
                if ext == '.docx':
                    ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
                    paragraphs = [''.join(t.text or '' for t in paragraph.iter() if t.tag == ns+'t') for paragraph in root.iter(ns+'p')]
                    parts.append('\n'.join(paragraphs) if paragraphs else ' '.join(root.itertext()))
                else:
                    parts.append(' '.join(t.text for t in root.iter() if t.text and t.text.strip()))
                if sum(map(len, parts)) > MAX_TEXT:
                    break
        value = '\n'.join(parts)
    elif ext == '.pdf':
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        if reader.is_encrypted and not reader.decrypt(''):
            return '', 'Name only: password-protected PDF'
        parts, length = [], 0
        for page in reader.pages:
            text = page.extract_text() or ''
            parts.append(text)
            length += len(text)
            if length > MAX_TEXT:
                break
        value = '\n'.join(parts)
    else:
        return '', 'Name only: unsupported content format'
    status = 'Partial: first 1 million characters' if len(value) > MAX_TEXT else ('Content indexed' if value.strip() else 'Name only: no readable text (scan may need OCR)')
    return value[:MAX_TEXT], status

def extraction_worker(pipe):
    logging.basicConfig(filename=str(BASE/'data'/'filefinder.log') if (BASE/'data').exists() else None,level=logging.ERROR)
    while True:
        try: path = pipe.recv()
        except EOFError: break
        try: result = extract(Path(path))
        except Exception as e: result = ('', 'Read error: ' + str(e)[:180])
        pipe.send(result)

class Extractor:
    def __init__(self):
        self.process = self.pipe = None

    def close(self):
        if self.process:
            if self.process.is_alive(): self.process.terminate()
            self.process.join(timeout=2)
            self.process.close()
            self.pipe.close()
            self.process = self.pipe = None

    def read(self, path, stop, timeout=15):
        if not self.process:
            ctx = multiprocessing.get_context('spawn')
            self.pipe, child = ctx.Pipe()
            self.process = ctx.Process(target=extraction_worker,args=(child,),daemon=True)
            try: self.process.start()
            except Exception:
                self.pipe.close(); self.process = self.pipe = None
                raise
            finally: child.close()
        try: self.pipe.send(str(path))
        except (BrokenPipeError,EOFError,OSError):
            self.close()
            return '', 'Read error: document reader stopped'
        deadline = time.monotonic() + timeout
        while not self.pipe.poll(.1):
            if stop.is_set() or time.monotonic() >= deadline or not self.process.is_alive():
                self.close()
                return '', 'Pending content' if stop.is_set() else 'Read error: text extraction timed out or stopped'
        try: return self.pipe.recv()
        except (EOFError, OSError):
            self.close()
            return '', 'Read error: document reader stopped'

class Index:
    def __init__(self, db):
        self.db = str(db)
        with self.connect() as c:
            c.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS roots(path TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS files(id INTEGER PRIMARY KEY, path TEXT UNIQUE, root TEXT, name TEXT, ext TEXT, size INTEGER, mtime INTEGER, content TEXT, status TEXT, seen TEXT);
            CREATE INDEX IF NOT EXISTS root_idx ON files(root);
            CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(name,content,content=files,content_rowid=id,tokenize='unicode61');
            CREATE TRIGGER IF NOT EXISTS ai AFTER INSERT ON files BEGIN INSERT INTO search(rowid,name,content) VALUES(new.id,new.name,new.content); END;
            CREATE TRIGGER IF NOT EXISTS ad AFTER DELETE ON files BEGIN INSERT INTO search(search,rowid,name,content) VALUES('delete',old.id,old.name,old.content); END;
            DROP TRIGGER IF EXISTS au;
            CREATE TRIGGER au AFTER UPDATE OF name,content ON files BEGIN
            INSERT INTO search(search,rowid,name,content) VALUES('delete',old.id,old.name,old.content);
            INSERT INTO search(rowid,name,content) VALUES(new.id,new.name,new.content); END;
            ''')

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.db, timeout=30)
        c.row_factory = sqlite3.Row
        c.create_function('casefold', 1, lambda value: (value or '').casefold(), deterministic=True)
        try:
            with c: yield c
        finally: c.close()

    def roots(self):
        with self.connect() as c:
            return [r[0] for r in c.execute('SELECT path FROM roots ORDER BY path')]

    def add(self, path):
        path = os.path.normpath(os.path.abspath(path))
        if not os.path.isdir(io_path(path)):
            raise ValueError('Choose an existing folder or drive.')
        for root in self.roots():
            try:
                common = os.path.commonpath([os.path.normcase(root), os.path.normcase(path)])
                if common in {os.path.normcase(root), os.path.normcase(path)}:
                    raise ValueError('This folder overlaps an existing search folder. Remove the existing entry first, or choose another folder.')
            except ValueError as e:
                if 'overlaps' in str(e):
                    raise
        with self.connect() as c:
            c.execute('INSERT OR IGNORE INTO roots VALUES(?)', (path,))

    def remove(self, path):
        with self.connect() as c:
            c.execute('DELETE FROM files WHERE root=?', (path,))
            c.execute('DELETE FROM roots WHERE path=?', (path,))

    def scan(self, stop, report, names_only=False):
        count = errors = 0
        for root in self.roots():
            if stop.is_set(): break
            if not os.path.isdir(io_path(root)):
                errors += 1
                report('Folder unavailable: ' + root)
                logging.warning('Folder unavailable: %s',root)
                continue
            stamp = str(time.time_ns())
            walk_errors = []
            report('Finding filenames: ' + root)
            visited = set()
            with self.connect() as c:
                for directory, dirs, names in os.walk(io_path(root), onerror=walk_errors.append, followlinks=False):
                    if os.name == 'nt':
                        directory = ('\\\\'+directory[8:]) if directory.startswith('\\\\?\\UNC\\') else directory.removeprefix('\\\\?\\')
                    resolved = os.path.normcase(os.path.realpath(directory))
                    if resolved in visited:
                        dirs[:] = []
                        continue
                    visited.add(resolved)
                    dirs[:] = [d for d in dirs if descend(Path(directory,d))]
                    for name in names:
                        if stop.is_set(): break
                        path = Path(directory, name)
                        try:
                            if path.is_symlink() or BASE in path.resolve().parents: continue
                            stat = os.stat(io_path(path))
                            attrs = getattr(stat,'st_file_attributes',0)
                            old = c.execute('SELECT size,mtime,status FROM files WHERE path=?',(str(path),)).fetchone()
                            if old and old['size']==stat.st_size and old['mtime']==stat.st_mtime_ns:
                                c.execute('UPDATE files SET seen=? WHERE path=?',(stamp,str(path)))
                            else:
                                status = 'Pending content'
                                if name.startswith('~$'):
                                    status = 'Name only: temporary Office lock file'
                                elif path.suffix.lower() not in TEXT | {'.pdf','.docx','.xlsx','.pptx','.odt','.ods','.odp'}:
                                    status = 'Name only: unsupported content format'
                                elif attrs & (0x1000 | 0x40000 | 0x400000):
                                    status = 'Name only: cloud file; download locally then refresh'
                                elif stat.st_size > MAX_BYTES:
                                    status = 'Name only: exceeds 32 MB content limit'
                                c.execute("""INSERT INTO files(path,root,name,ext,size,mtime,content,status,seen) VALUES(?,?,?,?,?,?,?,?,?)
                                ON CONFLICT(path) DO UPDATE SET root=excluded.root,name=excluded.name,ext=excluded.ext,size=excluded.size,mtime=excluded.mtime,content=excluded.content,status=excluded.status,seen=excluded.seen""",
                                (str(path),root,name,path.suffix.lower(),stat.st_size,stat.st_mtime_ns,'',status,stamp))
                            if old and old['status'].startswith('Name only: cloud') and not attrs & (0x1000 | 0x40000 | 0x400000):
                                c.execute("UPDATE files SET status='Pending content' WHERE path=?",(str(path),))
                            count += 1
                            if count % 100 == 0:
                                c.commit()
                                report(f'Finding filenames · {count:,} saved · {directory}')
                        except OSError as e:
                            walk_errors.append(str(e))
                    if stop.is_set(): break
                if not stop.is_set() and not walk_errors:
                    c.execute('DELETE FROM files WHERE root=? AND seen<>?',(root,stamp))
                errors += len(walk_errors)
                for error in walk_errors: logging.warning('Scan access issue: %s',error)
        report(f'{count:,} filenames checked. Reading document contents…')
        if names_only: return
        extractor = Extractor()
        completed = 0
        try:
            with self.connect() as c:
                pending = c.execute("SELECT id,path,size,mtime FROM files WHERE (status='Pending content' OR status LIKE 'Read error:%') AND name NOT LIKE '~$%'").fetchall()
            for row in pending:
                if stop.is_set(): break
                report(f'Reading text {completed+1:,}/{len(pending):,} · {Path(row["path"]).name}')
                content,status = extractor.read(row['path'],stop)
                # A file can be edited while its text is being read. Do not
                # attach an obsolete extraction to newer file metadata.
                try:
                    stat = os.stat(io_path(row['path']))
                    if stat.st_mtime_ns != row['mtime'] or stat.st_size != row['size']:
                        content,status = '', 'Pending content'
                except OSError:
                    content,status = '', 'Read error: file moved or unavailable'
                with self.connect() as c:
                    c.execute('UPDATE files SET content=?,status=? WHERE id=? AND size=? AND mtime=?',(content,status,row['id'],row['size'],row['mtime']))
                completed += 1
                if status.startswith('Read error'):
                    errors += 1
                    logging.warning('%s: %s',row['path'],status)
        finally: extractor.close()
        report(f'{"Paused" if stop.is_set() else "Index ready"} · {count:,} filenames checked · {completed:,} documents read · {errors} issues')

    def search(self, query, mode='Everywhere', ext='', limit=300):
        query = query.strip()
        phrase = len(query)>1 and query.startswith('"') and query.endswith('"')
        clean = query[1:-1] if phrase else query
        # Preserve combining marks used in Hindi and other writing systems.
        fts_terms = [t for t in re.split(r'[\s.,;:!?/\\_()\[\]{}"-]+',clean) if t]
        terms = fts_terms if any(ch.isalnum() for ch in clean) else []
        fts = '"'+clean.replace('"','""')+'"' if phrase else ' AND '.join('"'+t.replace('"','""')+'"*' for t in fts_terms)
        def pattern(value):
            return '%' + value.casefold().replace('!', '!!').replace('%','!%').replace('_','!_') + '%'
        conditions,args = [],[]
        if mode != 'Contents':
            pieces = [clean] if phrase or not terms else terms
            conditions.append('('+' AND '.join("casefold(name) LIKE ? ESCAPE '!'" for _ in pieces)+')')
            args.extend(pattern(t) for t in pieces)
        if mode != 'Filename' and fts_terms and terms:
            conditions.append('id IN (SELECT rowid FROM search WHERE search MATCH ?)')
            args.append('content : ('+fts+')')
        where = '('+' OR '.join(conditions)+')' if conditions else '0'
        if not query: where,args = '1',[]
        if ext.strip():
            extensions = ['.'+e.strip().lstrip('.').lower() for e in ext.split(',') if e.strip()]
            if extensions:
                where += ' AND ext IN ('+','.join('?' for _ in extensions)+')'
                args.extend(extensions)
        with self.connect() as c:
            return [dict(r) for r in c.execute("SELECT id,name,path,ext,size,mtime,status FROM files WHERE "+where+" ORDER BY CASE WHEN casefold(name) LIKE ? ESCAPE '!' THEN 0 ELSE 1 END,mtime DESC LIMIT ?",args+[pattern(clean),limit])]

    def detail(self, ident):
        with self.connect() as c:
            row = c.execute('SELECT * FROM files WHERE id=?', (ident,)).fetchone()
            return dict(row) if row else None

from filefinder_ui import App

if __name__=='__main__':
    multiprocessing.freeze_support()
    if len(sys.argv)>2 and sys.argv[1]=='--packaging-check':
        from packaging_check import run
        run(Index,sys.argv[2]); sys.exit(0)
    (BASE/'data').mkdir(exist_ok=True)
    logging.basicConfig(filename=str(BASE/'data'/'filefinder.log'),level=logging.WARNING,format='%(asctime)s %(levelname)s %(message)s')
    mutex = None
    if os.name == 'nt':
        import ctypes, hashlib
        # Give the desktop app its own taskbar identity instead of Python's.
        if not getattr(sys,'frozen',False):
            shell = ctypes.WinDLL('shell32')
            shell.SetCurrentProcessExplicitAppUserModelID.argtypes = [ctypes.c_wchar_p]
            shell.SetCurrentProcessExplicitAppUserModelID.restype = ctypes.c_long
            shell.SetCurrentProcessExplicitAppUserModelID('FileFinder.Desktop.2')
        kernel = ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.CreateMutexW.argtypes = [ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p]
        kernel.CreateMutexW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        key = hashlib.sha256(str(BASE).casefold().encode()).hexdigest()[:16]
        mutex = kernel.CreateMutexW(None,False,'Local\\FileFinder_'+key)
        if mutex and ctypes.get_last_error()==183:
            notice=tk.Tk(); notice.withdraw()
            messagebox.showinfo('FileFinder is already open','Use the existing FileFinder window. Close it before starting another copy.',parent=notice)
            notice.destroy(); kernel.CloseHandle(mutex); sys.exit(0)
    window=tk.Tk()
    def callback_error(kind,error,tb):
        logging.error('Application error',exc_info=(kind,error,tb))
        messagebox.showerror('FileFinder error',str(error))
    window.report_callback_exception=callback_error
    app=App(window,Index(BASE/'data'/'index.sqlite3'))
    if len(sys.argv)>1:
        app.query.set(sys.argv[1])
        if len(sys.argv)>2: app.ext.set(sys.argv[2])
        window.after(200,app.search)
    window.mainloop()
    if mutex: kernel.CloseHandle(mutex)
