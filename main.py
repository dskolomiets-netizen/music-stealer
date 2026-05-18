import spotipy
from spotipy.oauth2 import SpotifyOAuth
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
def extract_spotify_id(url):
    return url.split("/")[-1].split("?")[0]

client_id = "815743b24e9147f9b7b84078252addd0"
client_secret = "d648ee65934f4cc09bed86bfd3c5e88c"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope="playlist-read-private playlist-read-collaborative",
        open_browser=True,
        cache_path=".spotifycache"
    )
)

user = sp.current_user()
print(user["display_name"])


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
            items = []
            offset = 0

            while True:
                results = sp.playlist_items(
                    url,
                    offset=offset,
                    limit=100,
                    additional_types="track"
                )
                current_items = results.get("items", [])
                print(f"Получено: {len(current_items)}")
                if not current_items:
                    break
                items.extend(current_items)
                offset += 100

            print(f"Всего items: {len(items)}")

            for item in items:
                if not isinstance(item, dict):
                    print(f"[DEBUG] item is not dict: {type(item)}")
                    continue
                track = item.get("track") or item.get("episode") or item.get("item")
                if not track or not isinstance(track, dict):
                    continue
                # Пропускаем треки без id (удалённые/локальные файлы)
                if not track.get("id"):
                    continue
                artists = [artist.get("name", "Unknown") for artist in track.get("artists", [])]
                tracks_data.append({
                    "Название": track.get("name", "Unknown"),
                    "Исполнитель": ", ".join(artists),
                    "Альбом": track.get("album", {}).get("name", "Unknown"),
                    "Длительность (сек)": track.get("duration_ms", 0) // 1000
                })

            print(f"Треков после фильтрации: {len(tracks_data)}")

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