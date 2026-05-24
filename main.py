import pandas as pd
import tkinter as tk
from tkinter import messagebox
import re


# === UI ===
root = tk.Tk()
root.withdraw()


def ask_string(title, prompt):
    """Своё диалоговое окно с поддержкой вставки на любой раскладке."""
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.grab_set()

    tk.Label(dialog, text=prompt, padx=20, pady=10).pack()
    entry = tk.Entry(dialog, width=50)
    entry.pack(padx=20, pady=(0, 10))
    entry.focus_set()

    # Ctrl+V и Ctrl+м (русская раскладка) — оба работают
    def paste(e=None):
        try:
            entry.insert(tk.INSERT, dialog.clipboard_get())
        except Exception:
            pass

    entry.bind("<Control-v>", paste)
    # Для русской раскладки — ловим по keycode клавиши V (86),
    # т.к. tkinter не принимает кириллицу в bind()
    entry.bind("<Control-KeyPress>", lambda e: paste() if e.keycode == 86 else None)

    result = [None]

    def on_ok(e=None):
        result[0] = entry.get()
        dialog.destroy()

    def on_cancel(e=None):
        dialog.destroy()

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=(0, 10))
    tk.Button(btn_frame, text="OK", width=10, command=on_ok).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Отмена", width=10, command=on_cancel).pack(side=tk.LEFT, padx=5)

    entry.bind("<Return>", on_ok)
    entry.bind("<Escape>", on_cancel)

    dialog.wait_window()
    return result[0]


url = ask_string("Музыка", "Вставь ссылку:")
tablename = ask_string("Музыка", "Название файла:")

if not url:
    messagebox.showerror("Ошибка", "Ссылка не введена")
    exit()
if not tablename:
    tablename = "table"
tablename = re.sub(r'[\\/*?:"<>|]', "_", tablename)

from yamu import get_yandex_playlist
from spotify import get_spotify_tracks

tracks_data = []

try:
    if "music.yandex.ru" in url:
        tracks_data = get_yandex_playlist(url)

    elif "spotify" in url:
        tracks_data = get_spotify_tracks(url)

    else:
        raise ValueError("Ссылка не поддерживается")

    df = pd.DataFrame(tracks_data)
    df.to_excel(f"{tablename}.xlsx", index=False)
    messagebox.showinfo("Готово", f"Сохранено {len(tracks_data)} треков")

except Exception as e:
    messagebox.showerror("Ошибка", str(e))