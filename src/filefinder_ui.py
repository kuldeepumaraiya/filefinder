"""FileFinder's desktop interface. The index stays in filefinder.py."""
import os
import re
import queue
import threading
import time
import subprocess
import logging
import base64
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BG = '#f4f5f9'
WHITE = '#ffffff'
INK = '#202438'
MUTED = '#737a90'
LINE = '#e5e8f0'
ACCENT = '#6554d9'
SIDE = '#202238'
GROUPS = {
    'All files': '',
    'Documents': 'docx,doc,odt,txt,md,rtf,pdf',
    'Spreadsheets': 'xlsx,xls,csv,tsv,ods',
    'PDFs': 'pdf',
    'Images': 'png,jpg,jpeg,webp,gif,svg,bmp,tif,tiff',
    'Code': 'py,js,ts,tsx,jsx,html,css,json,java,c,cpp,h,cs,sql,yaml,yml,toml,ps1',
}

class App:
    def __init__(self, window, index):
        self.win, self.index = window, index
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.worker = None
        self.generation = 0
        self.preview_generation = 0
        self.rows = {}
        self.closing = False
        self._search_after = None
        self._stats_generation = 0
        self._active_query = ''
        self._sort = ('mtime', True)
        self._last_live_update = 0
        self.query = tk.StringVar()
        self.mode = tk.StringVar(value='Everywhere')
        self.ext = tk.StringVar()
        self.status = tk.StringVar(value='Ready to search your library')
        self.resultlabel = tk.StringVar(value='Your library')
        self.library_count = tk.StringVar(value='…')
        self.library_note = tk.StringVar(value='Checking the index')
        self.preview_name = tk.StringVar(value='Select a file')
        self.preview_meta = tk.StringVar(value='A quick look before you open it.')
        self.preview_path = tk.StringVar()
        self.coverage = tk.StringVar(value='')
        self.folder_path = tk.StringVar(value='Choose a folder to see its full path.')
        window.title('FileFinder 2.0 — Search your PC')
        assets=Path(__file__).resolve().parent/'assets'
        if (assets/'filefinder.ico').exists():
            try: window.iconbitmap(default=str(assets/'filefinder.ico'))
            except tk.TclError: logging.exception('Could not load the window icon')
        if (assets/'filefinder.png').exists():
            self.logo=tk.PhotoImage(master=window,data=base64.b64encode((assets/'filefinder.png').read_bytes()))
            window.iconphoto(True,self.logo)
        window.geometry('1320x820')
        window.minsize(1040,650)
        window.configure(bg=BG)
        self.style = ttk.Style(window)
        self.style.theme_use('clam')
        self.style.configure('.',font=('Segoe UI',10),background=BG,foreground=INK)
        self.style.configure('TFrame',background=BG)
        self.style.configure('Card.TFrame',background=WHITE)
        self.style.configure('TLabel',background=BG)
        self.style.configure('Card.TLabel',background=WHITE)
        self.style.configure('TButton',padding=(12,9),background=WHITE,borderwidth=0,foreground=INK)
        self.style.map('TButton',background=[('active','#eeedf9'),('disabled','#f1f2f6')],foreground=[('disabled','#a0a5b5')])
        self.style.configure('Primary.TButton',background=ACCENT,foreground=WHITE,font=('Segoe UI',10,'bold'))
        self.style.map('Primary.TButton',background=[('active','#5442c5'),('disabled','#b5ace8')],foreground=[('disabled',WHITE)])
        self.style.configure('Side.TButton',background='#30334d',foreground='#e8e9f5',padding=(10,9))
        self.style.map('Side.TButton',background=[('active','#404460'),('disabled','#292b40')],foreground=[('disabled','#737993')])
        self.style.configure('TCombobox',padding=7,fieldbackground=WHITE,background=WHITE,bordercolor=LINE,arrowcolor=MUTED)
        self.style.map('TCombobox',fieldbackground=[('readonly',WHITE)],selectbackground=[('readonly',WHITE)],selectforeground=[('readonly',INK)])
        self.style.configure('TEntry',padding=8,fieldbackground=WHITE,bordercolor=LINE)
        self.style.configure('Treeview',rowheight=48,font=('Segoe UI',10),background=WHITE,fieldbackground=WHITE,borderwidth=0)
        self.style.configure('Treeview.Heading',font=('Segoe UI',9,'bold'),background='#f8f9fc',foreground=MUTED,padding=(10,12),borderwidth=0)
        self.style.map('Treeview',background=[('selected','#eeebff')],foreground=[('selected','#493aaa')])
        self.style.map('Treeview.Heading',background=[('active','#eeedf9')])
        self.style.configure('Vertical.TScrollbar',background='#d3d7e4',troughcolor=WHITE,borderwidth=0,arrowsize=12)
        self.style.configure('Horizontal.TScrollbar',background='#d3d7e4',troughcolor=WHITE,borderwidth=0,arrowsize=12)
        self.style.configure('TProgressbar',background=ACCENT,troughcolor='#e8e5fa',borderwidth=0,thickness=3)
        self.style.configure('TPanedwindow',background=BG)
        self._sidebar()
        main = ttk.Frame(window,padding=(26,24,26,16))
        main.pack(side='left',fill='both',expand=True)
        main.columnconfigure(0,weight=1)
        main.rowconfigure(1,weight=1)
        header=ttk.Frame(main)
        header.grid(row=0,column=0,sticky='ew')
        self._header(header)
        body=ttk.Frame(main)
        body.grid(row=1,column=0,sticky='nsew')
        self._results(body)
        bottom = ttk.Frame(main)
        bottom.grid(row=2,column=0,sticky='ew',pady=(12,0))
        tk.Label(bottom,text='●',fg='#49a98c',bg=BG,font=('Segoe UI',10)).pack(side='left',padx=(0,7))
        self.status_widget = ttk.Label(bottom,textvariable=self.status,foreground=MUTED,font=('Segoe UI',9),wraplength=760)
        self.status_widget.pack(side='left',fill='x',expand=True)
        ttk.Label(bottom,text='Ctrl+F  search   ·   F5  refresh',foreground=MUTED,font=('Segoe UI',9)).pack(side='right',padx=(10,0))
        self.reload()
        self.refresh_stats()
        self.query.trace_add('write',self.schedule_search)
        self.mode.trace_add('write',self.schedule_search)
        self.ext.trace_add('write',self.schedule_search)
        window.bind('<Control-f>',self.focus_search)
        window.bind('<F5>',lambda e:self.scan())
        self.entry.bind('<Return>',lambda e:self.search())
        self.entry.bind('<Escape>',lambda e:self.query.set(''))
        self.tree.bind('<Return>',lambda e:self.open_file())
        window.protocol('WM_DELETE_WINDOW',self.close)
        self._poll_after = window.after(80,self.poll)
        window.after(150,self.search)
        self.entry.focus_set()

    def _sidebar(self):
        side = tk.Frame(self.win,bg=SIDE,width=238,padx=20,pady=24)
        side.pack(side='left',fill='y')
        side.pack_propagate(False)
        brand = tk.Frame(side,bg=SIDE)
        brand.pack(fill='x')
        if hasattr(self,'logo'):
            self.sidebar_logo=self.logo.subsample(8,8)
            tk.Label(brand,image=self.sidebar_logo,bg=SIDE).pack(side='left',padx=(0,10))
        tk.Label(brand,text='FileFinder',font=('Segoe UI',17,'bold'),fg=WHITE,bg=SIDE).pack(side='left')
        tk.Label(side,text='A little less looking.\nA lot more finding.',font=('Segoe UI',10),fg='#b4b9d0',bg=SIDE,justify='left').pack(anchor='w',pady=(18,24))
        stat = tk.Frame(side,bg='#2c2f48',padx=16,pady=14)
        stat.pack(fill='x')
        tk.Label(stat,textvariable=self.library_count,font=('Segoe UI',26,'bold'),fg=WHITE,bg='#2c2f48').pack(anchor='w')
        tk.Label(stat,text='FILES IN YOUR LIBRARY',font=('Segoe UI',8,'bold'),fg='#b4b9d0',bg='#2c2f48').pack(anchor='w',pady=(2,8))
        tk.Label(stat,textvariable=self.library_note,font=('Segoe UI',9),fg='#b4b9d0',bg='#2c2f48',wraplength=160,justify='left').pack(anchor='w')
        tk.Label(side,text='SEARCH LOCATIONS',font=('Segoe UI',8,'bold'),fg='#9099b8',bg=SIDE).pack(anchor='w',pady=(26,12))
        self.folderlist = tk.Listbox(side,bg=SIDE,fg='#dfe2f2',selectbackground='#393657',selectforeground=WHITE,bd=0,highlightthickness=0,font=('Segoe UI',10),activestyle='none',exportselection=False,height=6)
        self.folderlist.pack(fill='x')
        self.folderlist.bind('<<ListboxSelect>>',self.folder_selected)
        tk.Label(side,textvariable=self.folder_path,font=('Segoe UI',8),fg='#9099b8',bg=SIDE,wraplength=192,justify='left').pack(fill='x',pady=(8,12))
        self.addbtn = ttk.Button(side,text='+  Add folder or drive',style='Side.TButton',command=self.add)
        self.addbtn.pack(fill='x')
        self.removebtn = ttk.Button(side,text='Remove selected location',style='Side.TButton',command=self.remove,state='disabled')
        self.removebtn.pack(fill='x',pady=(7,0))
        footer = tk.Frame(side,bg=SIDE)
        footer.pack(side='bottom',fill='x')
        self.scanbtn = ttk.Button(footer,text='↻  Refresh index',style='Side.TButton',command=self.scan)
        self.scanbtn.pack(fill='x')
        self.pausebtn = ttk.Button(footer,text='Pause indexing',style='Side.TButton',command=self.pause,state='disabled')
        self.pausebtn.pack(fill='x',pady=(7,0))
        ttk.Button(footer,text='Help & shortcuts',style='Side.TButton',command=self.help).pack(fill='x',pady=(7,20))
        tk.Label(footer,text='LOCAL & PRIVATE',font=('Segoe UI',8,'bold'),fg='#92d8c2',bg=SIDE).pack(anchor='w')
        tk.Label(footer,text='Your files stay on this PC.\nFileFinder 2.0',font=('Segoe UI',9),fg='#9099b8',bg=SIDE,justify='left').pack(anchor='w',pady=(6,0))

    def _header(self, main):
        ttk.Label(main,text='Find your next file.',font=('Segoe UI',25,'bold'),foreground=INK).pack(anchor='w')
        ttk.Label(main,text='Search a name, a phrase, or something you remember from inside.',foreground=MUTED,font=('Segoe UI',10)).pack(anchor='w',pady=(5,12))
        shell = tk.Frame(main,bg=WHITE,highlightbackground=LINE,highlightthickness=1,padx=14,pady=8)
        shell.pack(fill='x')
        tk.Label(shell,text='⌕',bg=WHITE,fg=ACCENT,font=('Segoe UI',25)).pack(side='left',padx=(0,10))
        self.entry = tk.Entry(shell,textvariable=self.query,font=('Segoe UI',15),bg=WHITE,fg=INK,insertbackground=ACCENT,relief='flat',bd=0)
        self.entry.pack(side='left',fill='x',expand=True,ipady=5)
        ttk.Button(shell,text='Clear',command=lambda:self.query.set('')).pack(side='left',padx=(8,4))
        ttk.Button(shell,text='Search',style='Primary.TButton',command=self.search).pack(side='right')
        filterbar = ttk.Frame(main)
        filterbar.pack(fill='x',pady=(10,10))
        ttk.Label(filterbar,text='Look in',foreground=MUTED,font=('Segoe UI',9)).pack(side='left',padx=(0,8))
        self.mode_widget = ttk.Combobox(filterbar,textvariable=self.mode,values=['Everywhere','Filename','Contents'],state='readonly',width=12)
        self.mode_widget.pack(side='left')
        ttk.Label(filterbar,text='File type',foreground=MUTED,font=('Segoe UI',9)).pack(side='left',padx=(18,8))
        self.type_widget = ttk.Combobox(filterbar,textvariable=self.ext,values=['','pdf','docx','xlsx','pptx','txt','csv','jpg','png'],width=10)
        self.type_widget.pack(side='left')
        self.type_widget.bind('<Return>',lambda e:self.search())
        ttk.Label(filterbar,text='Try “faculty” or an "exact phrase"',foreground=MUTED,font=('Segoe UI',9)).pack(side='right')
        categories = ttk.Frame(main)
        categories.pack(fill='x',pady=(0,12))
        self.chips={}
        for label in GROUPS:
            button=tk.Button(categories,text=label,command=lambda name=label:self.category(name),bg=WHITE,fg=MUTED,activebackground='#eeebff',activeforeground=ACCENT,relief='flat',bd=0,font=('Segoe UI',9),padx=13,pady=7,cursor='hand2')
            button.pack(side='left',padx=(0,6))
            self.chips[label]=button
        self._set_chip('All files')
        progress_frame=tk.Frame(main,bg=LINE,height=3)
        progress_frame.pack(fill='x',pady=(0,14))
        progress_frame.pack_propagate(False)
        self.progress=ttk.Progressbar(progress_frame,mode='indeterminate')

    def _results(self, main):
        heading=ttk.Frame(main)
        heading.pack(fill='x',pady=(0,10))
        ttk.Label(heading,textvariable=self.resultlabel,font=('Segoe UI',12,'bold')).pack(side='left')
        ttk.Label(heading,text='Double-click a file to open',foreground=MUTED,font=('Segoe UI',9)).pack(side='right')
        self.pane=ttk.Panedwindow(main,orient='horizontal')
        self.pane.pack(fill='both',expand=True)
        results=tk.Frame(self.pane,bg=WHITE,highlightbackground=LINE,highlightthickness=1)
        self.pane.add(results,weight=3)
        self.tree=ttk.Treeview(results,columns=('name','ext','size'),show='headings',selectmode='browse',height=5)
        for key,label,width in [('name','FILE NAME',300),('ext','TYPE',70),('size','SIZE',80)]:
            self.tree.heading(key,text=label,anchor='w',command=lambda column=key:self.sort(column))
            self.tree.column(key,width=width,minwidth=60,stretch=key=='name',anchor='w')
        self.tree.tag_configure('alternate',background='#fafbfe')
        vs=ttk.Scrollbar(results,orient='vertical',command=self.tree.yview)
        hs=ttk.Scrollbar(results,orient='horizontal',command=self.tree.xview)
        self.tree.configure(yscrollcommand=vs.set,xscrollcommand=hs.set)
        hs.pack(side='bottom',fill='x'); vs.pack(side='right',fill='y')
        self.tree.pack(fill='both',expand=True)
        self.tree.bind('<<TreeviewSelect>>',self.preview)
        self.tree.bind('<Double-1>',lambda e:self.open_file())
        self.empty=tk.Frame(results,bg=WHITE)
        tk.Label(self.empty,text='No files here yet',font=('Segoe UI',15,'bold'),bg=WHITE,fg=INK).pack(pady=(0,8))
        self.empty_note=tk.Label(self.empty,text='Add a folder to build your library.',font=('Segoe UI',10),bg=WHITE,fg=MUTED,wraplength=300,justify='center')
        self.empty_note.pack()
        preview=tk.Frame(self.pane,bg=WHITE,highlightbackground=LINE,highlightthickness=1,width=320,padx=18,pady=14)
        self.pane.add(preview,weight=2)
        actions=tk.Frame(preview,bg=WHITE)
        actions.pack(side='bottom',fill='x',pady=(8,0))
        self.openbtn=ttk.Button(actions,text='Open file  ↗',style='Primary.TButton',command=self.open_file,state='disabled')
        self.openbtn.pack(fill='x',pady=(0,7))
        secondary=tk.Frame(actions,bg=WHITE)
        secondary.pack(fill='x')
        self.revealbtn=ttk.Button(secondary,text='Show in folder',command=self.reveal,state='disabled')
        self.revealbtn.pack(side='left',fill='x',expand=True,padx=(0,4))
        self.copybtn=ttk.Button(secondary,text='Copy path',command=self.copy,state='disabled')
        self.copybtn.pack(side='left',fill='x',expand=True,padx=(4,0))
        tk.Label(preview,text='FILE DETAILS',font=('Segoe UI',8,'bold'),fg=ACCENT,bg=WHITE).pack(anchor='w')
        self.name_label=tk.Label(preview,textvariable=self.preview_name,font=('Segoe UI',14,'bold'),fg=INK,bg=WHITE,justify='left',anchor='w',wraplength=300)
        self.name_label.pack(fill='x',pady=(8,5))
        tk.Label(preview,textvariable=self.preview_meta,font=('Segoe UI',9),fg=MUTED,bg=WHITE,anchor='w',justify='left').pack(fill='x')
        self.path_label=tk.Label(preview,textvariable=self.preview_path,font=('Segoe UI',9),fg=MUTED,bg=WHITE,justify='left',anchor='w',wraplength=300,height=2)
        self.path_label.pack(fill='x',pady=(8,5))
        self.coverage_label=tk.Label(preview,textvariable=self.coverage,font=('Segoe UI',9),fg='#37846e',bg=WHITE,justify='left',anchor='w',wraplength=300)
        self.coverage_label.pack(fill='x',pady=(0,7))
        tk.Frame(preview,bg=LINE,height=1).pack(fill='x',pady=(0,8))
        tk.Label(preview,text='TEXT PREVIEW',font=('Segoe UI',8,'bold'),fg=MUTED,bg=WHITE).pack(anchor='w',pady=(0,6))
        textframe=tk.Frame(preview,bg=WHITE)
        textframe.pack(fill='both',expand=True)
        self.text=tk.Text(textframe,wrap='word',height=6,width=24,bd=0,font=('Segoe UI',10),bg=WHITE,fg='#4d556f',padx=0,pady=0,spacing1=2,spacing3=5,state='disabled',highlightthickness=0)
        scrollbar=ttk.Scrollbar(textframe,command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right',fill='y'); self.text.pack(fill='both',expand=True)
        self.text.tag_configure('hit',background='#e9e2ff',foreground='#49349a')
        preview.bind('<Configure>',self.resize_preview)

    def resize_preview(self,event):
        width=max(120,event.width-40)
        for widget in (self.name_label,self.path_label,self.coverage_label): widget.configure(wraplength=width)

    def focus_search(self,event=None):
        self.entry.focus_set(); self.entry.selection_range(0,'end')
        return 'break'

    def _set_chip(self,name):
        for label,button in self.chips.items():
            button.configure(bg='#e9e5fd' if label==name else WHITE,fg=ACCENT if label==name else MUTED)

    def category(self,name):
        self.ext.set(GROUPS[name]); self._set_chip(name)

    def schedule_search(self,*args):
        if self.closing: return
        self.generation+=1
        if self._search_after: self.win.after_cancel(self._search_after)
        self._search_after=self.win.after(300,self.search)
        self._set_chip(next((name for name,value in GROUPS.items() if self.ext.get()==value),None))

    def reload(self):
        self.root_paths=self.index.roots()
        self.folderlist.delete(0,'end')
        for path in self.root_paths:
            self.folderlist.insert('end','▸  '+(Path(path).name or path))
        self.folder_path.set('Choose a folder to see its full path.' if self.root_paths else 'Add the folders you want to search.')
        self.removebtn.configure(state='disabled')

    def folder_selected(self,event=None):
        selection=self.folderlist.curselection()
        if selection:
            self.folder_path.set(self.root_paths[selection[0]])
            self.removebtn.configure(state='disabled' if self.is_scanning() else 'normal')

    def is_scanning(self):
        return bool(self.worker and self.worker.is_alive())

    def add(self):
        if self.is_scanning(): return
        path=filedialog.askdirectory(parent=self.win,title='Add a folder or drive to your library')
        if path:
            try: self.index.add(path); self.reload(); self.scan()
            except (ValueError,OSError) as e: messagebox.showinfo('Search locations',str(e),parent=self.win)

    def remove(self):
        if self.is_scanning(): return
        selected=self.folderlist.curselection()
        if selected:
            self.index.remove(self.root_paths[selected[0]])
            self.reload(); self.refresh_stats(); self.search()
            self.status.set('Location removed from the search library.')

    def scan(self):
        if self.closing or self.is_scanning(): return
        if not self.index.roots(): self.add(); return
        self.stop.clear()
        for b in (self.addbtn,self.removebtn,self.scanbtn): b.configure(state='disabled')
        self.pausebtn.configure(state='normal')
        self.progress.pack(fill='both',expand=True)
        self.progress.start(14)
        self.status.set('Finding files… You can keep searching.')
        def run():
            try:
                self.index.scan(self.stop,lambda s:self.events.put(('status',s)))
            except Exception as e:
                logging.exception('Index scan interrupted')
                self.events.put(('status','Index interrupted: '+str(e)))
            finally: self.events.put(('done',None))
        self.worker=threading.Thread(target=run,daemon=True); self.worker.start()

    def pause(self):
        self.stop.set(); self.pausebtn.configure(state='disabled')
        self.status.set('Pausing… Completed files are saved.')

    def search(self):
        if self.closing: return
        if self._search_after: self.win.after_cancel(self._search_after); self._search_after=None
        self.generation+=1
        generation=self.generation
        query,mode,ext=self.query.get().strip(),self.mode.get(),self.ext.get()
        self.resultlabel.set('Searching…')
        def run():
            try: self.events.put(('results',(generation,query,self.index.search(query,mode,ext))))
            except Exception as e:
                logging.exception('Search failed')
                self.events.put(('error',(generation,str(e))))
        threading.Thread(target=run,daemon=True).start()

    def refresh_stats(self):
        self._stats_generation+=1
        generation=self._stats_generation
        def run():
            try:
                with self.index.connect() as c:
                    row=c.execute("SELECT count(*) AS total, sum(status='Content indexed' OR status LIKE 'Partial:%') AS readable, sum(status='Pending content') AS pending FROM files").fetchone()
                    self.events.put(('stats',(generation,dict(row))))
            except Exception: logging.exception('Library statistics failed')
        threading.Thread(target=run,daemon=True).start()

    def poll(self):
        if self.closing: return
        for _ in range(100):
            try: kind,value=self.events.get_nowait()
            except queue.Empty: break
            if kind=='status':
                self.status.set(value)
                if time.monotonic()-self._last_live_update>2:
                    self._last_live_update=time.monotonic()
                    self.refresh_stats(); self.search()
            elif kind=='done':
                self.progress.stop(); self.progress.pack_forget()
                for b in (self.addbtn,self.scanbtn): b.configure(state='normal')
                self.folder_selected(); self.pausebtn.configure(state='disabled')
                self.refresh_stats(); self.search()
            elif kind=='stats':
                generation,stats=value
                if generation!=self._stats_generation: continue
                self.library_count.set(f'{stats["total"]:,}')
                self.library_note.set(f'{stats["readable"] or 0:,} with searchable text' + (f'\n{stats["pending"]:,} waiting for text' if stats['pending'] else ''))
            elif kind=='error':
                generation,error=value
                if generation==self.generation:
                    self.rows={}; self.tree.delete(*self.tree.get_children()); self.clear_preview()
                    self.resultlabel.set('Search could not finish')
                    self.status.set(error)
            elif kind=='results':
                generation,query,rows=value
                if generation!=self.generation: continue
                old_selection=self.tree.selection()
                selected=old_selection[0] if old_selection else None
                self._active_query=query
                self.rows={str(r['id']):r for r in rows}
                self.render_rows(selected)
                self.resultlabel.set(f'{len(rows):,} files'+(' · first 300 matches' if len(rows)==300 else '') if rows else 'No matching files')
                self.empty.place_forget()
                if not rows:
                    self.empty_note.configure(text='Try fewer words or another file type.\nRefresh the index if you added files.' if self.root_paths else 'Add a folder in the sidebar to start searching.')
                    self.empty.place(relx=.5,rely=.45,anchor='center')
            elif kind=='preview':
                generation,row,query=value
                if generation==self.preview_generation:
                    if row and self.tree.selection()==(str(row['id']),): self.render_preview(row,query)
                    elif row is None:
                        self.clear_preview(); self.status.set('File details unavailable. Refresh the index.')
        self._poll_after=self.win.after(80,self.poll)

    def render_rows(self,selected=None):
        self.tree.delete(*self.tree.get_children())
        key,reverse=self._sort
        rows=list(self.rows.values())
        if key!='mtime': rows.sort(key=lambda r:r[key].casefold() if isinstance(r[key],str) else r[key],reverse=reverse)
        for i,row in enumerate(rows):
            self.tree.insert('','end',iid=str(row['id']),values=(row['name'],row['ext'].lstrip('.').upper() or 'FILE',self.size(row['size'])),tags=('alternate',) if i%2 else ())
        self.clear_preview()
        if rows:
            ident=selected if selected in self.rows else str(rows[0]['id'])
            self.tree.selection_set(ident); self.tree.focus(ident)

    def sort(self,key):
        self._sort=(key,not self._sort[1] if self._sort[0]==key else False)
        selected=self.tree.selection()
        self.render_rows(selected[0] if selected else None)

    @staticmethod
    def size(n):
        for unit in ['B','KB','MB','GB']:
            if n<1024: return f'{n:,.0f} {unit}' if unit=='B' else f'{n:,.1f} {unit}'
            n/=1024
        return f'{n:.1f} TB'

    def selected(self):
        selection=self.tree.selection()
        return self.rows.get(selection[0]) if selection else None

    def clear_preview(self):
        self.preview_generation+=1
        self.preview_name.set('Select a file')
        self.preview_meta.set('A quick look before you open it.')
        self.preview_path.set(''); self.coverage.set('')
        self.text.configure(state='normal'); self.text.delete('1.0','end'); self.text.configure(state='disabled')
        for b in (self.openbtn,self.revealbtn,self.copybtn): b.configure(state='disabled')
        self.copybtn.configure(text='Copy path')

    def preview(self,event=None):
        row=self.selected()
        if not row: self.clear_preview(); return
        self.preview_generation+=1
        generation=self.preview_generation
        query=self._active_query
        self.preview_name.set(row['name']); self.preview_path.set(self.display_path(row['path']))
        self.preview_meta.set('Loading file details…')
        self.coverage.set('')
        self.text.configure(state='normal'); self.text.delete('1.0','end'); self.text.configure(state='disabled')
        for b in (self.openbtn,self.revealbtn,self.copybtn): b.configure(state='disabled')
        def run():
            try: detail=self.index.detail(row['id'])
            except Exception:
                logging.exception('Preview failed'); detail=None
            self.events.put(('preview',(generation,detail,query)))
        threading.Thread(target=run,daemon=True).start()

    def render_preview(self,row,query):
        self.preview_name.set(row['name'])
        try: modified=datetime.fromtimestamp(row['mtime']/1_000_000_000).strftime('%d %b %Y, %H:%M')
        except (ValueError,OSError): modified='Unknown date'
        self.preview_meta.set(f'{self.size(row["size"])}  ·  {row["ext"].lstrip(".").upper() or "FILE"}\nModified {modified}')
        self.preview_path.set(self.display_path(row['path'])); self.coverage.set(row['status'])
        self.coverage_label.configure(fg='#37846e' if row['status'].startswith(('Content','Partial')) else '#977738')
        content=row['content'] or ''
        tokens=[t for t in re.split(r'[\s.,;:!?/\\_()\[\]{}"-]+',query) if t]
        position=next((content.casefold().find(t.casefold()) for t in tokens if t.casefold() in content.casefold()),0)
        start=max(0,position-200)
        value=('…\n' if start else '')+content[start:start+14000]
        if not value:
            value='No text preview is available. Open the file to view it.\n\n'+row['status']
        elif start+14000<len(content): value+='\n…'
        self.text.configure(state='normal'); self.text.delete('1.0','end'); self.text.insert('1.0',value)
        for token in tokens[:25]:
            for match in re.finditer(re.escape(token),value,re.IGNORECASE):
                self.text.tag_add('hit',f'1.0+{match.start()}c',f'1.0+{match.end()}c')
        self.text.configure(state='disabled')
        for b in (self.openbtn,self.revealbtn,self.copybtn): b.configure(state='normal')

    @staticmethod
    def display_path(path):
        return '…'+path[-85:] if len(path)>88 else path

    def open_file(self):
        row=self.selected()
        if row:
            if row['ext'] in {'.exe','.msi','.bat','.cmd','.ps1','.vbs','.js','.scr','.com','.lnk'}:
                if not messagebox.askyesno('Open executable file?','This file can run code. Open it?',parent=self.win): return
            try: os.startfile(row['path'])
            except OSError as e: messagebox.showerror('Cannot open file',str(e),parent=self.win)

    def reveal(self):
        row=self.selected()
        if row:
            if not os.path.exists(row['path']): messagebox.showinfo('File moved','This file is no longer here. Refresh the index.',parent=self.win); return
            try: subprocess.Popen(['explorer.exe','/select,',row['path']])
            except OSError as e: messagebox.showerror('Cannot open folder',str(e),parent=self.win)

    def copy(self):
        row=self.selected()
        if row:
            self.win.clipboard_clear(); self.win.clipboard_append(row['path'])
            self.copybtn.configure(text='Path copied ✓')

    def help(self):
        messagebox.showinfo('FileFinder help','Add your folders in the sidebar. Filenames are saved first, then document text.\n\nSearch updates as you type. Choose Everywhere, Filename, or Contents. Category buttons filter file types; the type box accepts custom extensions, separated by commas. Use double quotes for a phrase.\n\nCtrl+F: focus search · Enter: search/open selected file\nEscape: clear search · F5: refresh index\n\nRefresh after files change. Pause keeps completed work.\n\nText support: PDF, modern Office, OpenDocument, plain text and code. Scans need OCR; old DOC/XLS/PPT and images are searchable by name. Cloud-only documents need to be downloaded locally for text search.\n\nContent limits: 32 MB, 1 million characters, 15 seconds per document. Everything is stored locally. Removing a location only removes it from the index.',parent=self.win)

    def close(self):
        if not self.closing:
            self.closing=True
            self.stop.set()
            if self._search_after: self.win.after_cancel(self._search_after)
            self.win.after_cancel(self._poll_after)
            self.progress.stop()
        if self.is_scanning():
            self.status.set('Saving progress and closing…')
            self.win.after(100,self.close)
        else: self.win.destroy()
