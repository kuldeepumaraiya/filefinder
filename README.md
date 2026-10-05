<p align="center">
  <img src="src/assets/filefinder.png" width="104" alt="FileFinder logo">
</p>
<h1 align="center">FileFinder</h1>
<p align="center"><strong>Remember a name. Remember a phrase. Find your file.</strong></p>
<p align="center">Search filenames and document contents on your Windows PC, with local indexing and in-app previews.</p>
<p align="center">
  <a href="https://github.com/kuldeepumaraiya/filefinder/actions/workflows/windows.yml"><img src="https://github.com/kuldeepumaraiya/filefinder/actions/workflows/windows.yml/badge.svg" alt="Windows build and tests"></a>
  <a href="https://github.com/kuldeepumaraiya/filefinder/releases/latest"><img src="https://img.shields.io/github/v/release/kuldeepumaraiya/filefinder?color=6654d9" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-6654d9" alt="MIT license"></a>
</p>
<p align="center">
  <a href="https://github.com/kuldeepumaraiya/filefinder/releases/download/v2.1.0/FileFinder-Windows-v2.1.0.zip"><strong>Download for Windows</strong></a> ·
  <a href="docs/USER_GUIDE.md">User guide</a> ·
  <a href="CHANGELOG.md">What's new</a> ·
  <a href="https://github.com/kuldeepumaraiya/filefinder/issues/new/choose">Report an issue</a>
</p>

## Find it, preview it, open it

| Feature | What you can do |
| --- | --- |
| **Search names and contents** | Find a file from part of its name, document words, or an exact phrase. |
| **Choose your folders** | Index selected folders or drives and filter results by file type. |
| **Jump between matches** | Use Previous / Next to highlight each mention, with a match count and text line number. |
| **Preview files** | Read extracted document text, view images, and browse rendered PDF pages. |
| **Keep it local** | Search with a local index. The app makes no network requests. |
| **Install or carry it** | Use the per-user installer or run the portable app. Python is bundled. |

## Download and install

### [Download FileFinder 2.1.0 for Windows](https://github.com/kuldeepumaraiya/filefinder/releases/download/v2.1.0/FileFinder-Windows-v2.1.0.zip)

**Windows 10 / 11 · 64-bit · No Python installation required**

1. Download **FileFinder-Windows-v2.1.0.zip** using the link above.
2. Right-click the ZIP and choose **Extract All**.
3. Open the extracted **FileFinder-Windows-v2.1.0** folder.
4. Double-click **Install.cmd**. If extensions are hidden, look for **Install** with type **Windows Command Script**.
5. Launch **FileFinder** from your desktop or Start Menu.

Your extracted folder should look like this:

```text
FileFinder-Windows-v2.1.0/
├── FileFinder.exe
├── _internal/
├── Install.cmd       ← run this
├── Install.ps1
├── licenses/
└── ...
```

> **Use the Windows download above.** GitHub's **Code → Download ZIP** provides source code for developers. Its `distribution/` folder contains installer templates without the executable.

The installer needs no administrator access. For portable use, open **FileFinder.exe** directly and keep `_internal` beside it. To pin the app, launch it, right-click its taskbar icon, and select **Pin to taskbar**. Keep the app in the same location after pinning.

Builds are currently unsigned. ARM and 32-bit Windows packages are not provided. [All releases and checksums →](https://github.com/kuldeepumaraiya/filefinder/releases)

## Your first search

1. **Add a folder** in the sidebar, such as Downloads or Documents.
2. **Search a name or phrase.** Filenames become available first; content indexing follows.
3. **Select a result** to read its text or open the **File preview** tab.
4. **Find each mention** using Previous / Next, or **F3 / Shift+F3**.

Press **Ctrl+F** to focus search and **F5** to refresh after files change. [Full user guide →](docs/USER_GUIDE.md)

## Supported files

| Files | Content search | Preview |
| --- | --- | --- |
| Text PDFs | Yes | Extracted text and rendered pages |
| DOCX, XLSX, PPTX, ODT, ODS, ODP | Yes | Extracted text |
| Text, CSV, Markdown and common code files | Yes | Text |
| Supported images | Filename only | Image |
| Scanned PDFs | Filename only | Rendered pages |
| Other files, including legacy DOC / XLS / PPT | Filename only | Open in the associated app |

Office previews show extracted text rather than the original page or worksheet layout. Match navigation jumps within indexed text inside FileFinder. OCR is not included. Content indexing is limited to 32 MB per file and one million characters. [All limits and troubleshooting →](docs/USER_GUIDE.md#content-support-and-limits)

## Privacy

Your index stays on your computer in `data/` beside the app. It can contain document text, so keep that folder private. Removing a search location leaves your original files intact. Public downloads contain no personal index or documents.

## Build and contribute

Built with Python, Tkinter, SQLite FTS5, pypdf, Pillow and PDFium.

- [Run from source, build and test](docs/DEVELOPMENT.md)
- [Contribute a fix or feature](CONTRIBUTING.md)
- [Read the changelog](CHANGELOG.md)

## License

FileFinder and its original logo are licensed under [MIT](LICENSE). Bundled dependencies retain their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.md) and [license files](licenses/).
