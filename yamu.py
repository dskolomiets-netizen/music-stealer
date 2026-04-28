from yandex_music import Client
import json
import os
import webbrowser
from tkinter import simpledialog, messagebox
import pyperclip
TOKEN_FILE = "yandex_token.json"
import re

def save_token(token):
    data = {
        "access_token": token.access_token,
        "refresh_token": token.refresh_token
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
        client = Client(token_data["access_token"]).init()
        return client

    # === Авторизация через device code ===
    def on_code(code):
        webbrowser.open(code.verification_url)
        pyperclip.copy(code.user_code)

        messagebox.showinfo("Yandex Music",f"Браузер открыт.\n\nВведи код:\n{code.user_code}")


    client = Client()
    token = client.device_auth(on_code=on_code)

    save_token(token)

    return client.init()


def get_yandex_playlist(url: str):
    client = get_client()

    try:
        parts = url.split("/")
        user = parts[4]
        playlist_id = parts[6]
    except Exception:
        raise ValueError("Неправильная ссылка на Яндекс Музыку")

    playlist = client.users_playlists(playlist_id, user)

    tracks_data = []

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

    return tracks_data

