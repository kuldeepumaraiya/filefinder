<p align="center"><img src="src/assets/filefinder.png" width="96" alt="FileFinder logo"></p>

# FileFinder

A private Windows desktop search app for finding files by their name or words inside them. Built with Python, Tkinter, SQLite FTS5, and pypdf. Licensed under MIT.

## Download and install

Download the Windows x64 ZIP from this repository's Releases page. Extract the entire folder before running it.

- **Install:** run `Install.cmd`. It installs for your Windows user, creates Start Menu and desktop shortcuts, and requires no administrator access.
- **Portable:** put the extracted folder in a writable location and open `FileFinder.exe`. Keep `_internal` next to the executable.
- **Taskbar:** launch the executable, right-click its taskbar icon, and choose **Pin to taskbar**.

The executable bundles its Python runtime. Builds are currently unsigned. Windows 10/11 x64 is the intended platform; ARM and 32-bit Windows builds are not provided. A Windows release is prepared with this source; published download availability depends on the release being uploaded.

## Use

1. Add folders or a drive in the sidebar. Indexing starts automatically.
2. Filenames become available first, followed by readable document text.
3. Enter a partial filename, words from a document, or an `"exact phrase"`.
4. Choose Everywhere, Filename, or Contents. Use category filters or enter extensions such as `pdf,docx`.
5. Select a result for its text preview; open it or show it in its folder.

Search updates as you type. Click a column heading to sort. Ctrl+F focuses search, Escape clears it, and F5 refreshes the index. Results are capped at 300; narrow the search to see more relevant files.

## Content support and limits

| Format | Search |
| --- | --- |
| All regular files | Filename |
| Text PDFs | Filename and extracted text |
| DOCX, XLSX, PPTX, ODT, ODS, ODP | Filename and extracted text |
| Plain text, CSV, Markdown, common source code | Filename and text |
| Images, scanned PDFs, old DOC/XLS/PPT, audio, video, archives | Filename; no OCR or archive extraction |

XLSX extraction reads worksheet values and shared strings, not Excel's display formatting. Cloud-only files must be downloaded locally for content search. Content extraction is limited to 32 MB per file, one million characters, and 15 seconds per document. Expanded document XML is capped at 64 MB. System/application/dependency folders and symbolic links are skipped. Refresh manually after files change; no automatic file watcher is included.

## Privacy

The app makes no network requests. It reads selected folders and stores extracted text in `data/index.sqlite3` next to the executable. Read issues are logged in `data/filefinder.log`. The index contains document text: keep it private. Removing a location removes its index entries and leaves the original files intact.

The public repository and distribution must never include a personal index, logs, or user documents. `.gitignore` excludes these files.

## Run from source

On Windows with Python 3.10 or newer, including Tkinter:

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python src\filefinder.py
```

## Build the executable

```powershell
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python scripts\build.py
```

Output: `dist/FileFinder/`. The script includes installation helpers and licenses in the Windows distribution. Build on Windows; PyInstaller does not cross-compile Windows executables from Linux.

## Tests

```powershell
.venv\Scripts\python tests\test_filefinder.py
.venv\Scripts\python tests\test_ui_v2.py
dist\FileFinder\FileFinder.exe --packaging-check build\packaging-result.json
```

The tests create temporary synthetic files and exercise filename/content search, PDFs, Office documents, index updates, Unicode, long Windows paths, previews, filters, and resizing. Desktop UI tests need an interactive Windows session.

## Contributing

Open an issue with steps to reproduce, the Windows version, and the file format involved. Do not upload private documents or search databases. For changes, open a pull request with a concise explanation and the test results.

## License

FileFinder code and original logo: [MIT](LICENSE). Bundled third-party components retain their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and `licenses/`.
