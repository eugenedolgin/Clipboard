import ctypes
import sys
import win32clipboard as w

FILE_PATH = r"X:\Folder\clipboard.bin"
GMEM_MOVEABLE = 0x0002
kernel32 = ctypes.windll.kernel32

def set_clipboard_text(text):
    data = text.encode("utf-16-le") + b"\x00\x00"  # CF_UNICODETEXT + нулевой терминатор
    h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not h_global:
        raise MemoryError("GlobalAlloc failed")
    ptr = kernel32.GlobalLock(h_global)
    ctypes.memmove(ptr, data, len(data))
    kernel32.GlobalUnlock(h_global)

    w.OpenClipboard()
    try:
        w.EmptyClipboard()
        w.SetClipboardData(w.CF_UNICODETEXT, h_global)  # после успешного вызова
        # система становится владельцем памяти — освобождать h_global вручную не нужно
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
	
	