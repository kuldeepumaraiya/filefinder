# Using FileFinder

[Download and install](../README.md#download-and-install) · [Back to FileFinder](../README.md)

## Use

1. Add folders or a drive in the sidebar. Indexing starts automatically.
2. Filenames become available first, followed by readable document text.
3. Enter a partial filename, words from a document, or an `"exact phrase"`.
4. Choose Everywhere, Filename, or Contents. Use category filters or enter extensions such as `pdf,docx`.
5. Select a result for its text preview; open it or show it in its folder.

Search updates as you type. Click a column heading to sort. Ctrl+F focuses search, Escape clears it, and F5 refreshes the index. Results are capped at 300; narrow the search to see more relevant files.

### Preview and find within a file

Select a result and use **Text & matches** to read its full indexed text. The find box starts with your search words and can be edited separately. **Previous / Next** jump between highlighted mentions, wrap at the ends, and show the match count and extracted-text line number. F3 moves forward; Shift+F3 moves backward. Double quotes match an exact phrase. Navigation covers the full indexed text, up to the extraction limit; it does not move the cursor in Word or another external application.

**File preview** shows basic image previews and rendered PDF pages with page controls. Word, Excel, PowerPoint and other documents use extracted text; original Office formatting is not rendered. Open the file for its full layout. Visual previews are limited to 64 MB files and the first frame of animated images.

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

## If a file is missing

1. Confirm its folder is included in the sidebar, then refresh with **F5**.
2. Try part of its filename with **Filename** selected. Clear category and extension filters.
3. Wait for content indexing to finish before searching words inside it.
4. For cloud storage, download the file locally first.
5. Check the format and size limits above. Scanned documents need OCR, which is not included.

## Updating and uninstalling

Close FileFinder, extract the latest Windows release, and run its **Install.cmd**. The installer preserves the existing installed app's `data/` folder. A portable copy has its own index; keep its `data/` folder when replacing the application files.

To uninstall, close FileFinder and remove its installed folder and shortcuts. Back up `data/` first if you want to retain your index.
