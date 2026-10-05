from pathlib import Path
import subprocess
import sys
import shutil

root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--onedir','--windowed','--name','FileFinder','--icon',str(root/'src/assets/filefinder.ico'),'--add-data',str(root/'src/assets')+';assets','--distpath',str(root/'dist'),'--workpath',str(root/'build'),'--specpath',str(root/'build'),str(root/'src/filefinder.py')],check=True,cwd=root)
dest=root/'dist/FileFinder'
for name in ('Install.ps1','Install.cmd','README.txt'):
    shutil.copy2(root/'distribution'/name,dest/name)
for name in ('LICENSE','THIRD_PARTY_NOTICES.md'):
    shutil.copy2(root/name,dest/name)
shutil.copytree(root/'licenses',dest/'licenses',dirs_exist_ok=True)
print('Windows distribution ready:',dest)
