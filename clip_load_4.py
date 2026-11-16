import sys
import pyperclip

FILE_PATH = r"X:\Folder\clipboard.bin"

def main():
    try:
        with open(FILE_PATH, "r", encoding="utf-8-sig") as f:
            text = f.read()
    except FileNotFoundError:
        print("Файл обмена не найден.")
        sys.exit(1)
    pyperclip.copy(text)
    print(f"Буфер обмена обновлён ({len(text)} символов).")

if __name__ == "__main__":
    main()
	