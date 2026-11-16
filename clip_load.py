import sys
import win32clipboard as w

FILE_PATH = r"X:\Folder\clipboard.bin"

def set_clipboard_text(text):
    w.OpenClipboard()
    try:
        w.EmptyClipboard()
        w.SetClipboardData(w.CF_UNICODETEXT, text)
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