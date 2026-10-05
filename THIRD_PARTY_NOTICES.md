# Third-party components

FileFinder includes or relies on these components. Their licenses remain separate from FileFinder's MIT license.

- Python 3.10 runtime: Python Software Foundation license and bundled component notices, including OpenSSL and libffi. See `licenses/Python-LICENSE.txt`.
- Tcl/Tk: BSD-style license terms in `licenses/TclTk-*.terms`.
- pypdf 6.18.0: BSD-3-Clause; see its license in `licenses/`.
- typing_extensions 4.16.0: Python Software Foundation license; see its license in `licenses/`.
- SQLite: public domain.
- PyInstaller bootloader: GPL with an exception permitting distribution of generated executables under the application's license. PyInstaller is used for packaging; see its upstream license and bootloader exception in `licenses/PyInstaller-COPYING.txt`.
- Microsoft Visual C++ runtime DLLs: included by the Python Windows distribution under Microsoft's redistribution terms.

Python does not need to be installed to run a packaged build. These notices cover the prepared Windows binary; building with a different Python version may require updating its bundled runtime notices.
