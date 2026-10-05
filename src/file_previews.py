"""Read-only, bounded basic image and PDF page previews."""
from pathlib import Path
import threading

PDF_LOCK=threading.Lock()

def render_file(path,page,width,height):
    try:
        from filefinder import io_path
        filename=io_path(path)
        if Path(filename).stat().st_size>64*1024*1024:
            return None,0,'Visual preview is limited to files under 64 MB. Open the file to view it.'
        if Path(path).suffix.lower()=='.pdf':
            import pypdfium2 as pdfium
            with PDF_LOCK:
                doc=pdfium.PdfDocument(filename)
                try:
                    count=len(doc)
                    pdfpage=doc[min(page,count-1)]
                    try:
                        w,h=pdfpage.get_size()
                        scale=min(width/w,height/h,2)
                        bitmap=pdfpage.render(scale=scale)
                        try:picture=bitmap.to_pil().copy()
                        finally:bitmap.close()
                    finally:pdfpage.close()
                    return picture,count,''
                finally:doc.close()
        if Path(path).suffix.lower() in {'.png','.jpg','.jpeg','.webp','.gif','.bmp','.tif','.tiff','.ico'}:
            from PIL import Image,ImageOps
            with Image.open(filename) as original:
                original.thumbnail((width,height))
                picture=ImageOps.exif_transpose(original).convert('RGB').copy()
            return picture,0,''
        return None,0,'Use Text & matches for Word, Excel, PowerPoint and text files. Original Office formatting is not rendered. Open file for its full layout.'
    except Exception as e:
        return None,0,'Preview unavailable: '+str(e)[:180]
