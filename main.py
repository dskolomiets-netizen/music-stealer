import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import tkinter as tk
from tkinter import simpledialog, messagebox
import re

from yamu import get_yandex_playlist


# === UI ===
root = tk.Tk()
root.withdraw()

url = simpledialog.askstring("Музыка", "Вставь ссылку:")
tablename = simpledialog.askstring("Музыка", "Название файла:")

if not url:
    messagebox.showerror("Ошибка", "Ссылка не введена")
    exit()

if not tablename:
    tablename = "table"

tablename = re.sub(r'[\\/*?:"<>|]', "_", tablename)


# === Spotify ===
client_id = "815743b24e9147f9b7b84078252addd0"
client_secret = "d648ee65934f4cc09bed86bfd3c5e88c"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
))


def get_all_items(results):
    items = results["items"]
    while results["next"]:
        results = sp.next(results)
        items.extend(results["items"])
    return items


tracks_data = []

try:
    # === YANDEX ===
    if "music.yandex.ru" in url:
        tracks_data = get_yandex_playlist(url)

    # === SPOTIFY ===
    elif "spotify" in url:

        if "playlist" in url:
            results = sp.playlist_tracks(url, limit=100)
            items = get_all_items(results)

            for item in items:
                track = item["track"]
                if track is None:
                    continue

                tracks_data.append({
                    "Название": track["name"],
                    "Исполнитель": ", ".join(a["name"] for a in track["artists"]),
                    "Альбом": track["album"]["name"],
                    "Длительность (сек)": track["duration_ms"] // 1000
                })

        elif "album" in url:
            results = sp.album_tracks(url)
            items = get_all_items(results)

            album_name = sp.album(url)["name"]

            for track in items:
                tracks_data.append({
                    "Название": track["name"],
                    "Исполнитель": ", ".join(a["name"] for a in track["artists"]),
                    "Альбом": album_name,
                    "Длительность (сек)": track["duration_ms"] // 1000
                })

        else:
            raise ValueError("Неизвестный тип ссылки Spotify")

    else:
        raise ValueError("Ссылка не поддерживается")

    # === SAVE ===
    df = pd.DataFrame(tracks_data)
    df.to_excel(f"{tablename}.xlsx", index=False)

    messagebox.showinfo("Готово", f"Сохранено {len(tracks_data)} треков")

except Exception as e:
    messagebox.showerror("Ошибка", str(e))