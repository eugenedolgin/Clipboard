import os
import sys
import win32clipboard as w

FILE_PATH = r"X:\Folder\clipboard.bin"

def get_clipboard_text():
    w.OpenClipboard()
    try:
        if not w.IsClipboardFormatAvailable(w.CF_UNICODETEXT):
            return None
        data = w.GetClipboardData(w.CF_UNICODETEXT)
        return data
    finally:
        w.CloseClipboard()

def main():
    text = get_clipboard_text()
    if text is None:
        print("Буфер обмена не содержит текста.")
        sys.exit(1)
    tmp = FILE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8-sig") as f:
        f.write(text)
    os.replace(tmp, FILE_PATH)  # атомарная запись
    print(f"Сохранено ({len(text)} символов).")

if __name__ == "__main__":
    main()