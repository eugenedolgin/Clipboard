import ctypes
import ctypes.wintypes as wt
import json
import os
import zipfile
import io

FILE_PATH = r"X:\Folder\clipboard.zip"

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

CF_LOCKED_HANDLES = {2, 3, 8, 17, 0x0082, 0x0083, 0x008E}  # bitmap, metafilepict, palette, enhanced metafile и display-варианты — не HGLOBAL, пропускаем

def save():
    if not user32.OpenClipboard(0):
        raise OSError("Не удалось открыть буфер обмена")
    try:
        formats = []
        fmt = 0
        while True:
            fmt = user32.EnumClipboardFormats(fmt)
            if fmt == 0:
                break
            if fmt in CF_LOCKED_HANDLES:
                continue  # GDI-хэндлы, не поток байтов
            h = user32.GetClipboardData(fmt)
            if not h:
                continue
            ptr = kernel32.GlobalLock(h)
            if not ptr:
                continue
            try:
                size = kernel32.GlobalSize(h)
                buf = ctypes.string_at(ptr, size)
            finally:
                kernel32.GlobalUnlock(h)
            # имя формата
            name_buf = ctypes.create_unicode_buffer(256)
            if user32.GetClipboardFormatNameW(fmt, name_buf, 256) > 0:
                name = name_buf.value
            else:
                std = {1:"CF_TEXT",13:"CF_UNICODETEXT",7:"CF_OEMTEXT",15:"CF_HDROP"}
                name = std.get(fmt, f"CF_{fmt}")
            formats.append({"id": fmt, "name": name, "data": buf})
    finally:
        user32.CloseClipboard()

    if not formats:
        raise SystemExit("Буфер обмена пуст.")

    bio = io.BytesIO()
    meta = []
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        for i, f in enumerate(formats):
            z.writestr(f"{i:03d}.bin", f["data"])
            meta.append({"id": f["id"], "name": f["name"], "file": f"{i:03d}.bin"})
        z.writestr("meta.json", json.dumps(meta, ensure_ascii=False))

    tmp = FILE_PATH + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(bio.getvalue())
    os.replace(tmp, FILE_PATH)
    print(f"Сохранено {len(formats)} форматов: " + ", ".join(m["name"] for m in meta))

if __name__ == "__main__":
    save()
    