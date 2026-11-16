import ctypes
import sys
import win32clipboard as w

FILE_PATH = r"X:\Folder\clipboard.bin"
GMEM_MOVEABLE = 0x0002

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
kernel32.GlobalFree.restype = ctypes.c_void_p
kernel32.GlobalFree.argtypes = [ctypes.c_void_p]


def set_clipboard_text(text):
    data = text.encode("utf-16-le") + b"\x00\x00"
    h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not h_global:
        raise MemoryError("GlobalAlloc failed")
    try:
        ptr = kernel32.GlobalLock(h_global)
        if not ptr:
            raise OSError(f"GlobalLock failed: {ctypes.get_last_error()}")
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(h_global)
    except BaseException:
        kernel32.GlobalFree(h_global)
        raise

    w.OpenClipboard()
    try:
        w.EmptyClipboard()
        w.SetClipboardData(w.CF_UNICODETEXT, h_global)
        # при успехе память принадлежит системе — не освобождаем
    except BaseException:
        kernel32.GlobalFree(h_global)
        raise
    finally:
        w.CloseClipboard()


def main():
    try:
        with open(FILE_PATH, "r", encoding="utf-8-sig") as f:
            text = f.read()
    except FileNotFoundError:
        print("Файл обмена не найден.")
        sys.exit(1)
    set_clipboard_text(text)
    print(f"Буфер обмена обновлён ({len(text)} символов).")

if __name__ == "__main__":
    main()