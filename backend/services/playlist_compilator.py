"""Spotify playlist compilator module."""

import time
from typing import Iterator, Dict, Any, Optional, List
from spotipy import Spotify
from spotipy.exceptions import SpotifyException


def safe_get_nested(data: dict, *keys: str) -> str | None:
    """Safely retrieve a string value from nested dictionaries."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, {})
        else:
            return None
    return data if isinstance(data, str) else None


def backoff_sleep(seconds: int) -> None:
    """Sleep with backoff."""
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
    """Get comma-separated string of artist names."""
    return ", ".join(a["name"] for a in (track.get("artists") or []))


def get_spotify_client() -> tuple[Spotify, str]:
    """Autentica usando access token en memoria (sin guardar archivos de caché)."""
    raise NotImplementedError("Use export_data(access_token) instead")


def export_data(access_token: str) -> tuple[List[Dict[str, Any]], List[List[str]]]:
    """Export all playlists and tracks from Spotify as JSON data using an access token.
    
    Args:
        access_token: Spotify OAuth2 access token
        
    Returns:
        Tuple of (playlists_data, tracks_data)
    """
    # Create Spotify client with access token (no cache files)
    sp = Spotify(auth=access_token)
    
    # Get current user info
    me = sp.current_user()
    if not me or not isinstance(me, dict) or "id" not in me:
        raise RuntimeError("Failed to fetch current user from Spotify; verify authentication.")
    username = me["id"]
    display_name = me.get("display_name") or username
    print(f"✅ Autenticado como: {display_name} ({username})")
    
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
            "tracks_total": (pl.get("tracks") or {}).get("total"),
            "href": pl.get("href"),
            "external_url": safe_get_nested(pl, "external_urls", "spotify"),
            "snapshot_id": pl.get("snapshot_id"),
        })

    # --- 2) Recoger "Canciones que te gustan" (Saved Tracks)
    print("📥 Descargando 'Canciones que te gustan'…")
    liked_items = list(paginate(lambda **kw: sp.current_user_saved_tracks(**kw)))
    liked_items = [it for it in liked_items if (it.get("track") or {}).get("type") == "track"]

    liked_pid = f"liked_{username}"
    liked_pname = "Canciones que te gustan"
    liked_owner = username
    liked_total = len(liked_items)

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

    # --- 3) Preparar encabezados y datos de tracks
    track_headers = [
        "playlist_id","playlist_name","playlist_owner_id",
        "added_at","added_by_id",
        "track_id","track_isrc","track_uri","track_url",
        "track_name","track_popularity","artists",
        "album_name","album_upc","album_release_date","duration_ms",
        "explicit","is_local"
    ]
    
    tracks_data: List[List[str]] = [track_headers]
    print("📥 Descargando canciones por playlist…")
    
    # 3a) Playlists reales
    for pl in playlists_rows:
        if pl["playlist_id"] == liked_pid:
            continue
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
                added_at, added_by_id or "",
                t.get("id") or "",
                safe_get_nested(t, "external_ids", "isrc") or "",
                t.get("uri") or "",
                safe_get_nested(t, "external_urls", "spotify") or "",
                t.get("name") or "",
                str(t.get("popularity") or ""),
                track_artists_str(t),
                safe_get_nested(t, "album", "name") or "",
                safe_get_nested(t, "album", "external_ids", "upc") or "",
                safe_get_nested(t, "album", "release_date") or "",
                str(t.get("duration_ms") or ""),
                str(t.get("explicit") or ""),
                str(is_local)
            ]
            tracks_data.append(row)
        time.sleep(0.1)

    # 3b) Volcar "Canciones que te gustan"
    for item in liked_items:
        added_at = item.get("added_at")
        t: Optional[Dict[str, Any]] = item.get("track")
        if not t:
            continue
        row = [
            liked_pid, liked_pname, liked_owner,
            added_at, None or "",
            t.get("id") or "",
            safe_get_nested(t, "external_ids", "isrc") or "",
            t.get("uri") or "",
            safe_get_nested(t, "external_urls", "spotify") or "",
            t.get("name") or "",
            str(t.get("popularity") or ""),
            track_artists_str(t),
            safe_get_nested(t, "album", "name") or "",
            safe_get_nested(t, "album", "external_ids", "upc") or "",
            safe_get_nested(t, "album", "release_date") or "",
            str(t.get("duration_ms") or ""),
            str(t.get("explicit") or ""),
            str(False)
        ]
        tracks_data.append(row)

    print("🎉 Export completo.")
    return playlists_rows, tracks_data
