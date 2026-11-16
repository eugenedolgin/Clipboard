import ctypes
import json
import zipfile

FILE_PATH = r"X:\Folder\clipboard.zip"

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

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
            fmt = m["id"]
            # зарегистрированные форматы (id >= 0xC000) на другой машине могут иметь другой id
            if fmt >= 0xC000:
                fmt = user32.RegisterClipboardFormatW(m["name"])
                if fmt == 0:
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
	