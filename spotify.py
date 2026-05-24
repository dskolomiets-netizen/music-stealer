import spotipy
from spotipy.oauth2 import SpotifyOAuth

client_id = "815743b24e9147f9b7b84078252addd0"
client_secret = "d648ee65934f4cc09bed86bfd3c5e88c"

# sp создаётся только при первом вызове get_spotify_tracks,
# а не при импорте модуля — иначе авторизация запрашивается сразу
_sp = None

def _get_sp():
    global _sp
    if _sp is None:
        _sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri="http://127.0.0.1:8888/callback",
                scope="playlist-read-private playlist-read-collaborative",
                open_browser=True,
                cache_path=".spotifycache"
            )
        )
    return _sp


def get_all_items(results):
    items = results["items"]
    while results["next"]:
        results = _get_sp().next(results)
        items.extend(results["items"])
    return items


def get_spotify_tracks(url: str):
    tracks_data = []

    if "playlist" in url:
        items = []
        offset = 0
        while True:
            results = _get_sp().playlist_items(
                url,
                offset=offset,
                limit=100,
                additional_types="track"
            )
            current_items = results.get("items", [])
            if not current_items:
                break
            items.extend(current_items)
            offset += 100

        for item in items:
            if not isinstance(item, dict):
                continue
            track = item.get("track") or item.get("episode") or item.get("item")
            if not track or not isinstance(track, dict):
                continue
            if not track.get("id"):
                continue
            artists = [a.get("name", "Unknown") for a in track.get("artists", [])]
            tracks_data.append({
                "Название": track.get("name", "Unknown"),
                "Исполнитель": ", ".join(artists),
                "Альбом": track.get("album", {}).get("name", "Unknown"),
                "Длительность (сек)": track.get("duration_ms", 0) // 1000
            })

    elif "album" in url:
        results = _get_sp().album_tracks(url)
        items = get_all_items(results)
        album_name = _get_sp().album(url)["name"]
        for track in items:
            tracks_data.append({
                "Название": track["name"],
                "Исполнитель": ", ".join(a["name"] for a in track["artists"]),
                "Альбом": album_name,
                "Длительность (сек)": track["duration_ms"] // 1000
            })

    else:
        raise ValueError("Неизвестный тип ссылки Spotify")

    return tracks_data