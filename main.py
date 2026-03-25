import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd

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

# === ВВОД ССЫЛКИ ===
url = input("Вставь ссылку на плейлист или альбом: ").strip()

tracks_data = []

try:
    if "playlist" in url:
        results = sp.playlist_tracks(url)
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

        album_info = sp.album(url)
        album_name = album_info["name"]

        for track in items:
            tracks_data.append({
                "Название": track["name"],
                "Исполнитель": ", ".join(a["name"] for a in track["artists"]),
                "Альбом": album_name,
                "Длительность (сек)": track["duration_ms"] // 1000
            })

    else:
        raise ValueError("Это не похоже на ссылку Spotify (ни плейлист, ни альбом)")

    df = pd.DataFrame(tracks_data)
    df.to_csv("table.csv", index=False)

    print(f"Готово. Сохранено {len(tracks_data)} треков в table.csv")

except Exception as e:
    print("Что-то пошло не так:")
    print(e)