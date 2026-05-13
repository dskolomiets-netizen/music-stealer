from yandex_music import Client
import json
import os
import re
import webbrowser
import requests
from tkinter import messagebox
import pyperclip
from urllib.parse import urlparse

TOKEN_FILE = "yandex_token.json"


def save_token(token):
    # token — объект OAuthToken с полями access_token, refresh_token, expires_in
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

    # === Авторизация через Device Flow (по документации библиотеки) ===
    def on_code(code):
        webbrowser.open(code.verification_url)
        pyperclip.copy(code.user_code)
        messagebox.showinfo(
            "Yandex Music",
            f"Браузер открыт.\n\nВведи код:\n{code.user_code}"
        )

    client = Client()
    token = client.device_auth(on_code=on_code)  # возвращает OAuthToken
    save_token(token)
    client.init()  # инициализируем тот же клиент, у которого уже есть токен
    return client


def resolve_lk_playlist(lk_id: str, token: str):
    """
    Пытается получить плейлист по lk.UUID через прямые запросы к API.
    Яндекс не документирует этот эндпоинт, поэтому перебираем кандидатов.
    """
    headers = {
        "Authorization": f"OAuth {token}",
        "X-Yandex-Music-Client": "YandexMusicAndroid/23020251",
    }
    uuid = lk_id.replace("lk.", "")

    candidates = [
        # .ru домен (найден в DevTools)
        f"https://api.music.yandex.ru/playlists/{lk_id}",
        f"https://api.music.yandex.ru/playlists/{uuid}",
        f"https://api.music.yandex.ru/share/playlist/{lk_id}",
        f"https://api.music.yandex.ru/share/playlist/{uuid}",
        f"https://api.music.yandex.ru/share/{lk_id}",
        f"https://api.music.yandex.ru/share/{uuid}",
        # .net домен (старый)
        f"https://api.music.yandex.net/share/playlist/{lk_id}",
        f"https://api.music.yandex.net/share/playlist/{uuid}",
        f"https://api.music.yandex.net/share/{lk_id}",
        f"https://api.music.yandex.net/share/{uuid}",
        # web handlers
        f"https://music.yandex.ru/handlers/playlist.jsx?shareToken={lk_id}",
        f"https://music.yandex.ru/handlers/playlist.jsx?shareToken={uuid}",
    ]

    for url in candidates:
        resp = requests.get(url, headers=headers, timeout=8)
        print(f"[DEBUG] {resp.status_code} {url}")
        if resp.status_code == 200:
            print(f"[DEBUG] Успешный ответ: {resp.text[:300]}")
            data = resp.json()
            return data.get("result", data)

    raise ValueError(
        f"Не удалось найти рабочий эндпоинт для плейлиста '{lk_id}'.\n"
        f"Яндекс не предоставляет публичный API для lk.UUID ссылок.\n\n"
        f"Решение: открой плейлист в браузере → F12 → Network → найди запрос\n"
        f"с треками → скинь его URL."
    )


def tracks_from_playlist_data(playlist_data: dict):
    tracks_data = []
    for item in playlist_data.get("tracks", []):
        track = item.get("track", item) if isinstance(item, dict) else item
        if not track:
            continue
        artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
        albums = track.get("albums", [])
        album_title = albums[0].get("title", "—") if albums else "—"
        tracks_data.append({
            "Название": track.get("title", "—"),
            "Исполнитель": artists,
            "Альбом": album_title,
            "Длительность (сек)": track.get("durationMs", 0) // 1000
        })
    return tracks_data


def get_yandex_tracks(url: str):
    client = get_client()
    token_data = load_token()
    access_token = token_data["access_token"] if token_data else None

    parsed = urlparse(url)
    path = parsed.path
    print(f"[DEBUG] Parsed path: {path}")

    tracks_data = []

    album_match = re.search(r'/album/(\d+)', path)
    old_match   = re.search(r'/users/([^/]+)/playlists/(\d+)', path)
    lk_match    = re.search(r'/playlists/(lk\.[^/?]+)', path)

    if album_match:
        album_id = album_match.group(1)
        print(f"[DEBUG] Album — id: {album_id}")
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
        print(f"[DEBUG] Playlist (old) — user: {user}, id: {playlist_id}")
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
        lk_id = lk_match.group(1)
        print(f"[DEBUG] Playlist (lk UUID) — id: {lk_id}")

        # lk.UUID — это ссылки «Поделиться» из браузера. Яндекс не открывает
        # их через мобильный/desktop API — данные грузятся через SSR в HTML.
        # Единственный lk.UUID который решается через API — «Мне нравится»
        # (liked tracks), для него есть прямой метод в библиотеке.
        # lk.UUID данные грузятся через SSR — парсим HTML страницы
        import re as _re
        import requests as _req
        import json as _json

        print("[DEBUG] Парсим HTML страницы для lk.UUID...")
        token_data = load_token()
        headers = {
            "Authorization": f"OAuth {token_data['access_token']}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ru,en;q=0.9",
        }
        resp = _req.get(f"https://music.yandex.ru/playlists/{lk_id}", headers=headers, timeout=15)
        print(f"[DEBUG] HTML status: {resp.status_code}, size: {len(resp.text)}")

        # Яндекс вкладывает начальные данные в window.__INITIAL_DATA__ или похожие переменные
        patterns = [
            r"window\.__INITIAL_DATA__\s*=\s*({.+?});\s*</script>",
            r"window\.__DATA__\s*=\s*({.+?});\s*</script>",
            r"window\.__SSR_DATA__\s*=\s*({.+?});\s*</script>",
            r'<script[^>]+type="application/json"[^>]*>({.+?})</script>',
        ]

        playlist_json = None
        for pat in patterns:
            m = _re.search(pat, resp.text, _re.DOTALL)
            if m:
                try:
                    playlist_json = _json.loads(m.group(1))
                    print(f"[DEBUG] Нашли данные по паттерну: {pat[:40]}")
                    print(f"[DEBUG] Ключи: {list(playlist_json.keys())[:10]}")
                    break
                except Exception:
                    continue

        if not playlist_json:
            # Последний fallback — liked tracks если это Мне нравится
            print("[DEBUG] SSR не нашли, пробуем liked tracks...")
            liked = client.users_likes_tracks()
            if not liked or not liked.tracks_ids:
                raise ValueError(
                    "Не удалось получить данные плейлиста."
                    "Яндекс Музыка загружает lk.UUID только через браузер (SSR)."
                    "Решение: открой плейлист → три точки → скопируй ссылку"
                    "вида music.yandex.ru/users/ИМЯ/playlists/ЧИСЛО"
                )
            track_ids = [str(t.id) if hasattr(t, "id") else str(t) for t in liked.tracks_ids]
            all_tracks = []
            for i in range(0, len(track_ids), 1000):
                all_tracks.extend(client.tracks(track_ids[i:i+1000]))
            for track in all_tracks:
                if track:
                    tracks_data.append({
                        "Название": track.title,
                        "Исполнитель": ", ".join(a.name for a in track.artists),
                        "Альбом": track.albums[0].title if track.albums else "—",
                        "Длительность (сек)": track.duration_ms // 1000
                    })
        else:
            # Ищем треки в найденном JSON
            def find_tracks(obj, depth=0):
                if depth > 6 or not isinstance(obj, (dict, list)):
                    return []
                if isinstance(obj, list):
                    results = []
                    for x in obj:
                        results.extend(find_tracks(x, depth+1))
                    return results
                if "title" in obj and "artists" in obj and "durationMs" in obj:
                    return [obj]
                found = []
                for v in obj.values():
                    found.extend(find_tracks(v, depth+1))
                return found

            raw_tracks = find_tracks(playlist_json)
            print(f"[DEBUG] Найдено треков в SSR JSON: {len(raw_tracks)}")
            for track in raw_tracks:
                artists = ", ".join(
                    a.get("name", "") for a in track.get("artists", [])
                    if isinstance(a, dict)
                )
                albums = track.get("albums", [])
                album_title = albums[0].get("title", "—") if albums else "—"
                tracks_data.append({
                    "Название": track.get("title", "—"),
                    "Исполнитель": artists,
                    "Альбом": album_title,
                    "Длительность (сек)": track.get("durationMs", 0) // 1000
                })

    else:
        raise ValueError(
            f"Не удалось распознать ссылку Яндекс Музыки.\n"
            f"Путь URL: {path}\n"
            f"Поддерживается:\n"
            f"  Альбом:    music.yandex.ru/album/ЧИСЛО\n"
            f"  Плейлист:  music.yandex.ru/users/ИМЯ/playlists/ЧИСЛО\n"
            f"  Плейлист:  music.yandex.ru/playlists/lk.UUID"
        )

    return tracks_data


get_yandex_playlist = get_yandex_tracks