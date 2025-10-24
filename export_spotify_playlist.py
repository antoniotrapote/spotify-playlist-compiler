import csv
import time
import os
from typing import Iterator, Dict, Any, Optional, Tuple, List
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

def safe_get_nested(data: dict, *keys: str) -> str | None:
    """Safely retrieve a string value from nested dictionaries."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, {})
        else:
            return None
    return data if isinstance(data, str) else None

# ===== Configuración =====
# + user-library-read para acceder a "Canciones que te gustan"
SCOPES = "playlist-read-private playlist-read-collaborative user-library-read"
CACHE_DIR = ".caches"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_export_dir(username: str) -> str:
    """Create and return the export directory for the given username."""
    export_dir = f"{username}_downloads"
    os.makedirs(export_dir, exist_ok=True)
    return export_dir

def backoff_sleep(seconds: int):
    time.sleep(max(1, int(seconds)))

def paginate(fetch_fn, key="items", limit=50, **kwargs) -> Iterator[Dict[str, Any]]:
    """Iterador para recorrer páginas de la API."""
    offset = 0
    while True:
        try:
            page = fetch_fn(limit=limit, offset=offset, **kwargs)
        except SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", "3"))
                backoff_sleep(retry_after)
                continue
            raise
        items = page.get(key, []) or []
        for it in items:
            yield it
        if page.get("next"):
            offset += limit
            time.sleep(0.05)
        else:
            break

def track_artists_str(track: Dict[str, Any]) -> str:
    return ", ".join(a["name"] for a in (track.get("artists") or []))

def get_spotify_client() -> Tuple[Spotify, str]:
    """Autentica y gestiona caches por usuario."""
    load_dotenv()
    temp_cache = os.path.join(CACHE_DIR, ".cache_temp")
    sp_temp = Spotify(auth_manager=SpotifyOAuth(scope=SCOPES, cache_path=temp_cache))
    me = sp_temp.current_user()
    username = me["id"]
    print(f"✅ Autenticado como: {me.get('display_name') or username} ({username})")
    user_cache = os.path.join(CACHE_DIR, f".cache_{username}")
    if os.path.exists(temp_cache) and not os.path.exists(user_cache):
        os.rename(temp_cache, user_cache)
    sp = Spotify(auth_manager=SpotifyOAuth(scope=SCOPES, cache_path=user_cache))
    return sp, username

def export_all() -> None:
    """Export all playlists and tracks from Spotify to CSV files."""
    sp, username = get_spotify_client()
    export_dir = get_export_dir(username)

    # --- 1) Recoger playlists "reales"
    playlists_rows: List[Dict[str, Any]] = []
    print("📥 Descargando playlists…")
    for pl in paginate(sp.current_user_playlists):
        playlists_rows.append({
            "playlist_id": pl["id"],
            "name": pl["name"],
            "public": pl.get("public"),
            "collaborative": pl.get("collaborative"),
            "owner_id": safe_get_nested(pl, "owner", "id"),
            "owner_name": safe_get_nested(pl, "owner", "display_name"),
            # total es numérico → no usar safe_get_nested aquí
            "tracks_total": (pl.get("tracks") or {}).get("total"),
            "href": pl.get("href"),
            "external_url": safe_get_nested(pl, "external_urls", "spotify"),
            "snapshot_id": pl.get("snapshot_id"),
        })

    # --- 2) Recoger "Canciones que te gustan" (Saved Tracks) una vez
    print("📥 Descargando 'Canciones que te gustan'…")
    liked_items = list(paginate(lambda **kw: sp.current_user_saved_tracks(**kw)))
    # Filtrar a solo canciones (por consistencia)
    liked_items = [it for it in liked_items if (it.get("track") or {}).get("type") == "track"]

    liked_pid = f"liked_{username}"
    liked_pname = "Canciones que te gustan"
    liked_owner = username
    liked_total = len(liked_items)

    # Añadir la pseudo-playlist ANTES de escribir el CSV de playlists
    playlists_rows.append({
        "playlist_id": liked_pid,
        "name": liked_pname,
        "public": False,
        "collaborative": False,
        "owner_id": liked_owner,
        "owner_name": liked_owner,
        "tracks_total": liked_total,
        "href": None,
        "external_url": None,
        "snapshot_id": None,
    })

    # --- 3) Escribir playlists.csv una sola vez (ya incluye la de liked)
    playlists_file = os.path.join(export_dir, f"playlists_{username}.csv")
    with open(playlists_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = list(playlists_rows[0].keys()) if playlists_rows else [
            "playlist_id","name","public","collaborative","owner_id","owner_name",
            "tracks_total","href","external_url","snapshot_id"
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in playlists_rows:
            w.writerow(row)
    print(f"💾 Guardado: {playlists_file} ({len(playlists_rows)} playlists)")

    # --- 4) Escribir tracks.csv (playlists reales + liked)
    track_headers = [
        "playlist_id","playlist_name","playlist_owner_id",
        "added_at","added_by_id",
        "track_id","track_isrc","track_uri","track_url",
        "track_name","track_popularity","artists",
        "album_name","album_upc","album_release_date","duration_ms",
        "explicit","is_local"
    ]
    tracks_file = os.path.join(export_dir, f"tracks_{username}.csv")
    out = open(tracks_file, "w", newline="", encoding="utf-8")
    w = csv.writer(out)
    w.writerow(track_headers)

    print("📥 Descargando canciones por playlist…")
    # 4a) Playlists reales
    for pl in playlists_rows:
        if pl["playlist_id"] == liked_pid:
            continue  # saltamos la liked aquí; la volcamos en 4b
        pid = pl["playlist_id"]
        pname = pl["name"]
        owner_id = pl["owner_id"]

        def fetch_items(**kw):
            return sp.playlist_items(pid, **kw)

        for item in paginate(fetch_items):
            added_at = item.get("added_at")
            added_by_id = (item.get("added_by") or {}).get("id")
            is_local = item.get("is_local", False)
            t: Optional[Dict[str, Any]] = item.get("track")
            if not t or t.get("type") != "track":
                continue
            row = [
                pid, pname, owner_id,
                added_at, added_by_id,
                t.get("id"),
                safe_get_nested(t, "external_ids", "isrc"),
                t.get("uri"),
                safe_get_nested(t, "external_urls", "spotify"),
                t.get("name"), t.get("popularity"),
                track_artists_str(t),
                safe_get_nested(t, "album", "name"),
                safe_get_nested(t, "album", "external_ids", "upc"),
                safe_get_nested(t, "album", "release_date"),
                t.get("duration_ms"), t.get("explicit"), is_local
            ]
            w.writerow(row)
        time.sleep(0.1)

    # 4b) Volcar "Canciones que te gustan" desde liked_items ya descargados
    for item in liked_items:
        added_at = item.get("added_at")
        t: Optional[Dict[str, Any]] = item.get("track")
        if not t:
            continue
        row = [
            liked_pid, liked_pname, liked_owner,
            added_at, None,  # added_by_id no aplica en saved tracks
            t.get("id"),
            safe_get_nested(t, "external_ids", "isrc"),
            t.get("uri"),
            safe_get_nested(t, "external_urls", "spotify"),
            t.get("name"), t.get("popularity"),
            track_artists_str(t),
            safe_get_nested(t, "album", "name"),
            safe_get_nested(t, "album", "external_ids", "upc"),
            safe_get_nested(t, "album", "release_date"),
            t.get("duration_ms"), t.get("explicit"), False
        ]
        w.writerow(row)

    out.close()
    print(f"💾 Guardado: {tracks_file}")
    print("🎉 Export completo.")
    print(f"📁 Archivos guardados en: {export_dir}/")


if __name__ == "__main__":
    export_all()