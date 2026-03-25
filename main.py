import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd

client_id = "815743b24e9147f9b7b84078252addd0"
client_secret = "d648ee65934f4cc09bed86bfd3c5e88c"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
))

url = "https://open.spotify.com/album/1TtdtRpeNYliHviOnhWdL7"

def get_all_items(results):
    items = results["items"]
    while results["next"]:
        results = sp.next(results)
        items.extend(results["items"])
    return items

tracks_data = []

if "playlist" in url:
    results = sp.playlist_items(playlist_id=('track',))
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
    raise ValueError("Ссылка должна быть на плейлист или альбом")

df = pd.DataFrame(tracks_data)
df.to_csv("playlist.csv", index=False)

print("Готово. Таблица создана.")