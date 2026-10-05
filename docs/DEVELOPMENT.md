# Developing FileFinder

[Back to FileFinder](../README.md) · [Contributing](../CONTRIBUTING.md)

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
.venv\Scripts\python tests\test_match_navigation.py
dist\FileFinder\FileFinder.exe --packaging-check build\packaging-result.json
```

The tests create temporary synthetic files and exercise filename/content search, PDFs, Office documents, index updates, Unicode, long Windows paths, previews, filters, and resizing. Desktop UI tests need an interactive Windows session.

## Project layout

| Folder | Purpose |
| --- | --- |
| `src/` | Search engine, desktop interface, preview renderer and app assets |
| `tests/` | Synthetic document, search, interface and preview checks |
| `scripts/` | Windows packaging script |
| `distribution/` | Installer templates copied into the packaged app |
| `docs/` | User and developer guides |
| `licenses/` | Bundled dependency license notices |

## Publishing a Windows package

Build and run the packaged check on Windows. Package the contents of `dist/FileFinder/` together, including `FileFinder.exe`, `_internal`, `Install.cmd`, `Install.ps1` and license files. Do not launch the distribution normally before packaging it: doing so can create a private `data/` folder. Never publish an index, logs or personal documents.

Keep the versioned download links in the README and installer templates aligned with the release. Include ZIP checksums and a short changelog. GitHub Actions builds and checks the app on Windows for pushes and pull requests.
