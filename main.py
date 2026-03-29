import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import traceback
import tkinter as tk
from tkinter import simpledialog, messagebox

# === UI ===
root = tk.Tk()
root.withdraw()

url = simpledialog.askstring("Spotify", "Вставь ссылку:")
tablename = simpledialog.askstring("Spotify", "Вставь название таблицы:")
if not url:
    messagebox.showerror("Ошибка", "Ссылка не введена")
    exit()

# === Spotify ===
client_id = "815743b24e9147f9b7b84078252addd0"
client_secret = "d648ee65934f4cc09bed86bfd3c5e88c"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
))

tracks_data = []

try:
    if "playlist" in url:
        items = []
        results = sp.playlist_tracks(url)
        while True:
            items.extend(results["items"])
            if results["next"]:
                results = sp.next(results)
            else:
                break

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
        items = []
        results = sp.album_tracks(url)
        album_name = sp.album(url)["name"]
        while True:
            items.extend(results["items"])
            if results["next"]:
                results = sp.next(results)
            else:
                break

        for track in items:
            tracks_data.append({
                "Название": track["name"],
                "Исполнитель": ", ".join(a["name"] for a in track["artists"]),
                "Альбом": album_name,
                "Длительность (сек)": track["duration_ms"] // 1000
            })

    else:
        raise ValueError("Это не ссылка Spotify")

    df = pd.DataFrame(tracks_data)
    df.to_excel(f"{tablename}.xlsx", index=False)

    messagebox.showinfo("Готово", f"Сохранено {len(tracks_data)} треков")

except Exception as e:
    messagebox.showerror("Ошибка", str(e))
    print(traceback.format_exc())