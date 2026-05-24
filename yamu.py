from yandex_music import Client
import json
import os
import re
import webbrowser
from tkinter import messagebox
import pyperclip
from urllib.parse import urlparse

TOKEN_FILE = "yandex_token.json"


def save_token(token):
    data = {
        "access_token": token.access_token,
        "refresh_token": token.refresh_token,
        "expires_in": token.expires_in,
    }
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_client():
    token_data = load_token()
    if token_data:
        return Client(token_data["access_token"]).init()

    def on_code(code):
        webbrowser.open(code.verification_url)
        pyperclip.copy(code.user_code)
        messagebox.showinfo(
            "Yandex Music",
            f"Браузер открыт.\n\nВведи код:\n{code.user_code}"
        )

    client = Client()
    token = client.device_auth(on_code=on_code)
    save_token(token)
    client.init()
    return client


def get_yandex_tracks(url: str):
    client = get_client()

    parsed = urlparse(url)
    path = parsed.path

    tracks_data = []

    album_match = re.search(r'/album/(\d+)', path)
    old_match   = re.search(r'/users/([^/]+)/playlists/(\d+)', path)
    lk_match    = re.search(r'/playlists/([^/?]+)', path)

    if album_match:
        album_id = album_match.group(1)
        album = client.albums_with_tracks(album_id)
        album_title = album.title or "—"
        for volume in album.volumes:
            for track in volume:
                if not track:
                    continue
                tracks_data.append({
                    "Название": track.title,
                    "Исполнитель": ", ".join(a.name for a in track.artists),
                    "Альбом": album_title,
                    "Длительность (сек)": track.duration_ms // 1000
                })

    elif old_match:
        user = old_match.group(1)
        playlist_id = old_match.group(2)
        playlist = client.users_playlists(playlist_id, user)
        for item in playlist.tracks:
            track = item.track
            if not track:
                continue
            tracks_data.append({
                "Название": track.title,
                "Исполнитель": ", ".join(a.name for a in track.artists),
                "Альбом": track.albums[0].title if track.albums else "—",
                "Длительность (сек)": track.duration_ms // 1000
            })

    elif lk_match:
        # Для lk.UUID ссылок поддерживается только «Мне нравится»
        liked = client.users_likes_tracks()
        if not liked or not liked.tracks_ids:
            raise ValueError("Список «Мне нравится» пуст или недоступен.")
        track_ids = [
            str(t.id) if hasattr(t, "id") else str(t)
            for t in liked.tracks_ids
        ]
        all_tracks = []
        for i in range(0, len(track_ids), 1000):
            all_tracks.extend(client.tracks(track_ids[i:i + 1000]))
        for track in all_tracks:
            if track:
                tracks_data.append({
                    "Название": track.title,
                    "Исполнитель": ", ".join(a.name for a in track.artists),
                    "Альбом": track.albums[0].title if track.albums else "—",
                    "Длительность (сек)": track.duration_ms // 1000
                })

    else:
        raise ValueError(
            f"Не удалось распознать ссылку Яндекс Музыки.\n"
            f"Путь URL: {path}\n\n"
            f"Поддерживается:\n"
            f"  Альбом:    music.yandex.ru/album/ЧИСЛО\n"
            f"  Плейлист:  music.yandex.ru/users/ИМЯ/playlists/ЧИСЛО\n"
            f"  Мне нравится: music.yandex.ru/playlists/lk.UUID"
        )

    return tracks_data


get_yandex_playlist = get_yandex_tracks