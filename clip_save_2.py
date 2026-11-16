import ctypes
import ctypes.wintypes as wt
import json
import os
import io
import zipfile

FILE_PATH = r"X:\Personal\Clipboard\clipboard.zip"

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32

# --- прототипы: ОБЯЗАТЕЛЬНО на 64-битном Python ---
user32.OpenClipboard.argtypes = [wt.HWND]
user32.OpenClipboard.restype = wt.BOOL
user32.CloseClipboard.restype = wt.BOOL
user32.EnumClipboardFormats.argtypes = [wt.UINT]
user32.EnumClipboardFormats.restype = wt.UINT
user32.GetClipboardData.argtypes = [wt.UINT]
user32.GetClipboardData.restype = ctypes.c_void_p      # 64-битный HANDLE
user32.SetClipboardData.argtypes = [wt.UINT, ctypes.c_void_p]
user32.SetClipboardData.restype = ctypes.c_void_p
user32.EmptyClipboard.restype = wt.BOOL
user32.IsClipboardFormatAvailable.argtypes = [wt.UINT]
user32.GetClipboardFormatNameW.argtypes = [wt.UINT, wt.LPWSTR, wt.INT]
user32.GetClipboardFormatNameW.restype = wt.INT

kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalLock.restype = ctypes.c_void_p          # 64-битный указатель
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.restype = wt.BOOL
kernel32.GlobalSize.argtypes = [ctypes.c_void_p]
kernel32.GlobalSize.restype = ctypes.c_size_t          # SIZE_T, не int
kernel32.GlobalAlloc.argtypes = [wt.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalFree.argtypes = [ctypes.c_void_p]

gdi32.GetDIBits.argtypes = [wt.HDC, wt.HBITMAP, wt.UINT, wt.UINT,
                             ctypes.c_void_p, ctypes.c_void_p, wt.UINT]
gdi32.GetDIBits.restype = wt.INT
gdi32.GetEnhMetaFileBits.argtypes = [wt.HENHMETAFILE, wt.UINT, ctypes.c_void_p]
gdi32.GetEnhMetaFileBits.restype = wt.UINT
# ----------------------------------------------------

CF_BITMAP, CF_PALETTE, CF_DIB, CF_DIBV5 = 2, 9, 8, 17
CF_ENHMETAFILE, CF_METAFILEPICT = 14, 3

class RGBQUAD(ctypes.Structure):
    _fields_ = [("rgbBlue", ctypes.c_ubyte),
                ("rgbGreen", ctypes.c_ubyte),
                ("rgbRed", ctypes.c_ubyte),
                ("rgbReserved", ctypes.c_ubyte)]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", ctypes.c_ulong),
                ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long),
                ("biPlanes", ctypes.c_ushort),
                ("biBitCount", ctypes.c_ushort),
                ("biCompression", ctypes.c_ulong),
                ("biSizeImage", ctypes.c_ulong),
                ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long),
                ("biClrUsed", ctypes.c_ulong),
                ("biClrImportant", ctypes.c_ulong)]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER),
                ("bmiColors", RGBQUAD * 256)]

def bitmap_to_dib(hbmp, hbmp_pal=0):
    """Конвертирует HBITMAP в CF_DIB (BITMAPINFOHEADER + биты)."""
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    if not gdi32.GetDIBits(None, hbmp, 0, 0, None, ctypes.byref(bmi), 0):
        return None
    if bmi.bmiHeader.biSizeImage == 0:
        bmi.bmiHeader.biSizeImage = abs(bmi.bmiHeader.biHeight) * (
            ((bmi.bmiHeader.biWidth * bmi.bmiHeader.biBitCount + 31) // 32) * 4)
    size = bmi.bmiHeader.biSizeImage
    buf = ctypes.create_string_buffer(size)
    if not gdi32.GetDIBits(None, hbmp, 0, abs(bmi.bmiHeader.biHeight), buf,
                          ctypes.byref(bmi), 0):
        return None
    return ctypes.string_at(bmi, ctypes.sizeof(BITMAPINFOHEADER)) + buf.raw[:size]
    

'''
def bitmap_to_dib(hbmp, hbmp_pal=0):
    class BMI(ctypes.Structure):
        _fields_ = [("bmiHeader", wt.BITMAPINFOHEADER), ("bmiColors", wt.RGBQUAD * 256)]
    bmi = BMI()
    bmi.bmiHeader.biSize = ctypes.sizeof(wt.BITMAPINFOHEADER)
    if not gdi32.GetDIBits(None, hbmp, 0, 0, None, ctypes.byref(bmi), 0):
        return None
    size = bmi.bmiHeader.biSizeImage or (abs(bmi.bmiHeader.biHeight)
        * (((bmi.bmiHeader.biWidth * bmi.bmiHeader.biBitCount + 31) // 32) * 4))
    bmi.bmiHeader.biSizeImage = size
    buf = ctypes.create_string_buffer(size)
    if not gdi32.GetDIBits(None, hbmp, 0, abs(bmi.bmiHeader.biHeight), buf,
                          ctypes.byref(bmi), 0):
        return None
    return ctypes.string_at(bmi, ctypes.sizeof(wt.BITMAPINFOHEADER)) + buf.raw[:size]
'''
def enhmetafile_to_bits(hemf):
    size = gdi32.GetEnhMetaFileBits(hemf, 0, None)
    if not size:
        return None
    buf = ctypes.create_string_buffer(size)
    if not gdi32.GetEnhMetaFileBits(hemf, size, buf):
        return None
    return buf.raw

def save():
    if not user32.OpenClipboard(None):
        raise OSError("Не удалось открыть буфер обмена")
    try:
        entries = []
        fmt = 0
        while True:
            fmt = user32.EnumClipboardFormats(fmt)
            if fmt == 0:
                break
            h = user32.GetClipboardData(fmt)
            if not h:
                continue
            name_buf = ctypes.create_unicode_buffer(256)
            if user32.GetClipboardFormatNameW(fmt, name_buf, 256) > 0:
                name = name_buf.value
            else:
                std = {1:"CF_TEXT", 7:"CF_OEMTEXT", 13:"CF_UNICODETEXT",
                       8:"CF_DIB", 17:"CF_DIBV5", 15:"CF_HDROP",
                       2:"CF_BITMAP", 14:"CF_ENHMETAFILE", 3:"CF_METAFILEPICT",
                       9:"CF_PALETTE", 10:"CF_PENDATA"}
                name = std.get(fmt, f"CF_{fmt}")

            if fmt == CF_BITMAP:
                data = bitmap_to_dib(h, user32.GetClipboardData(CF_PALETTE) or 0)
                if data:
                    entries.append(["hglobal", CF_DIB, "CF_DIB", data])
            elif fmt == CF_ENHMETAFILE:
                data = enhmetafile_to_bits(h)
                if data:
                    entries.append(["enhmeta", CF_ENHMETAFILE, "CF_ENHMETAFILE", data])
            elif fmt in (CF_METAFILEPICT, CF_PALETTE):
                continue
            else:
                ptr = kernel32.GlobalLock(h)
                if not ptr:
                    continue
                try:
                    size = kernel32.GlobalSize(h)
                    data = ctypes.string_at(ptr, size)
                finally:
                    kernel32.GlobalUnlock(h)
                entries.append(["hglobal", fmt, name, data])
    finally:
        user32.CloseClipboard()

    if not entries:
        raise SystemExit("Буфер обмена пуст.")

    bio = io.BytesIO()
    meta = []
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        for i, (kind, fmt_id, name, data) in enumerate(entries):
            fn = f"{i:03d}.bin"
            z.writestr(fn, data)
            meta.append({"kind": kind, "fmt": fmt_id, "name": name, "file": fn})
        z.writestr("meta.json", json.dumps(meta, ensure_ascii=False))

    tmp = FILE_PATH + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(bio.getvalue())
    os.replace(tmp, FILE_PATH)
    print(f"Сохранено {len(entries)} форматов: " + ", ".join(m["name"] for m in meta))

if __name__ == "__main__":
    save()
	