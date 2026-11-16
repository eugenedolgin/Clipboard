import ctypes
import json
import zipfile
import ctypes.wintypes as wt

FILE_PATH = r"X:\Personal\Clipboard\clipboard.zip"  

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32

user32.OpenClipboard.argtypes = [wt.HWND]
user32.OpenClipboard.restype = wt.BOOL
user32.CloseClipboard.restype = wt.BOOL
user32.EmptyClipboard.restype = wt.BOOL
user32.GetClipboardData.argtypes = [wt.UINT]
user32.GetClipboardData.restype = ctypes.c_void_p
user32.SetClipboardData.argtypes = [wt.UINT, ctypes.c_void_p]
user32.SetClipboardData.restype = ctypes.c_void_p
user32.RegisterClipboardFormatW.argtypes = [wt.LPCWSTR]
user32.RegisterClipboardFormatW.restype = wt.UINT

kernel32.GlobalAlloc.argtypes = [wt.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
kernel32.GlobalFree.argtypes = [ctypes.c_void_p]

gdi32.SetEnhMetaFileBits.argtypes = [wt.UINT, ctypes.c_void_p]
gdi32.SetEnhMetaFileBits.restype = wt.HENHMETAFILE
gdi32.DeleteEnhMetaFile.argtypes = [wt.HENHMETAFILE]


GMEM_MOVEABLE = 0x0002

def load():
    with zipfile.ZipFile(FILE_PATH) as z:
        meta = json.loads(z.read("meta.json"))
        entries = [(m, z.read(m["file"])) for m in meta]

    if not user32.OpenClipboard(0):
        raise OSError("Не удалось открыть буфер обмена")
    try:
        user32.EmptyClipboard()
        for m, data in entries:
            fmt = m["fmt"]
            if fmt >= 0xC000:  # зарегистрированный формат: id на другой машине другой
                fmt = user32.RegisterClipboardFormatW(m["name"])
                if fmt == 0:
                    continue

            if m["kind"] == "enhmeta":
                hemf = gdi32.SetEnhMetaFileBits(len(data), data)
                if not hemf or not user32.SetClipboardData(fmt, hemf):
                    if hemf:
                        gdi32.DeleteEnhMetaFile(hemf)
                continue

            h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
            if not h:
                continue
            ptr = kernel32.GlobalLock(h)
            ctypes.memmove(ptr, data, len(data))
            kernel32.GlobalUnlock(h)
            if not user32.SetClipboardData(fmt, h):
                kernel32.GlobalFree(h)
    finally:
        user32.CloseClipboard()
    print(f"Восстановлено {len(entries)} форматов.")

if __name__ == "__main__":
    load()
	