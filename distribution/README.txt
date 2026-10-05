FILEFINDER 2.1.0 — WINDOWS x64

IF THIS FOLDER CONTAINS ONLY INSTALL SCRIPTS:
You downloaded the source-code ZIP (filefinder-main). This distribution
directory contains templates for developers and does not include the app.
Download the ready-to-use Windows package instead:
https://github.com/kuldeepumaraiya/filefinder/releases/download/v2.1.0/FileFinder-Windows-v2.1.0.zip
After extracting it, Install.cmd, FileFinder.exe, and _internal appear together.
Run that Install.cmd. Do not use Code > Download ZIP for the Windows app.

Copy this entire folder to another Windows 10/11 x64 computer, or extract
the ZIP before launching. No separate Python installation is needed.

INSTALL: double-click Install.cmd. It copies the app to your user's
LocalAppData\Programs\FileFinder and creates desktop and Start Menu shortcuts.
It needs no administrator privileges. Close FileFinder before an update.
Existing search data in the installed folder is preserved during updates.

PORTABLE: open FileFinder.exe directly from a writable folder.
Keep _internal beside the executable. You may skip installation entirely.

PIN: open the app, right-click its taskbar icon, select Pin to taskbar.
Keep the installed or portable app in the same location after pinning.

USE: add folders in the sidebar; filenames are indexed first, then contents.
Search a filename or document words. Use quotes for a phrase. Filter with
category buttons or extensions. Select a result for its preview.
Refresh after files change. Ctrl+F focuses search; F5 refreshes.

PRIVACY: no uploads. Your local index and logs are written to data/ beside
the executable. The distribution starts empty and includes no personal index.
Removing a folder from search never removes your source files.

TEXT SUPPORT: text PDFs, DOCX/XLSX/PPTX, OpenDocument, text and code.
Scanned PDFs/images and old DOC/XLS/PPT are filename-only. No OCR is included.
Limits: 32 MB per file, 1 million characters, 15 seconds per document.

This build is unsigned. License: MIT for FileFinder; dependency licenses are
in licenses/ and THIRD_PARTY_NOTICES.md.

UNINSTALL: close the app, delete its installed app folder and the desktop/
Start Menu shortcuts. Back up data/ first if you want to keep the search index.

PREVIEWS: Text & matches contains full indexed text, with an independent
find box, Previous/Next matches, counts, and line positions. F3/Shift+F3
navigate matches. File preview renders images and PDF pages. Office files
use text previews; Open file shows their original layout.

