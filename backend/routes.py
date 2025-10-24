"""API routes."""

import secrets
import json
from flask import Blueprint, jsonify, session, request, redirect, Response, stream_with_context
from backend.auth import get_auth_url, exchange_code_for_token, refresh_access_token
from spotipy import Spotify

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/auth/login", methods=["GET"])
def auth_login():
    """Initiate Spotify OAuth2 login flow."""
    state = secrets.token_urlsafe(32)
    session["auth_state"] = state
    auth_url = get_auth_url(state)
    return jsonify({"auth_url": auth_url}), 200


@api.route("/auth/callback", methods=["GET"])
def auth_callback():
    """Handle Spotify OAuth2 callback."""
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    
    # Check for errors
    if error:
        return redirect(f"/?error={error}")
    
    # Verify code is present
    if not code:
        return redirect("/?error=no_code")
    
    # Verify state for CSRF protection
    if state != session.get("auth_state"):
        return redirect("/?error=invalid_state")
    
    try:
        # Exchange code for access token
        token_data = exchange_code_for_token(code)
        
        # Store token in session (in-memory, not on disk)
        session["access_token"] = token_data["access_token"]
        session["refresh_token"] = token_data.get("refresh_token")
        session["expires_in"] = token_data.get("expires_in", 3600)
        
        return redirect("/")
    except Exception as e:
        return redirect(f"/?error={str(e)}")


@api.route("/auth/logout", methods=["POST"])
def auth_logout():
    """Logout user and clear session tokens."""
    session.clear()
    return jsonify({"success": True}), 200


@api.route("/auth/status", methods=["GET"])
def auth_status():
    """Check if user is authenticated."""
    is_authenticated = "access_token" in session
    return jsonify({"authenticated": is_authenticated}), 200


@api.route("/export/progress", methods=["GET"])
def export_with_progress():
    """Stream export progress to client using Server-Sent Events."""
    access_token = session.get("access_token")
    
    if not access_token:
        return jsonify({"error": "Not authenticated"}), 401
    
    def generate_progress():
        """Generator function that yields progress updates."""
        try:
            from backend.spotify_export.exporter import paginate, safe_get_nested, track_artists_str
            from typing import List, Dict, Any, Optional
            
            # Create Spotify client
            sp = Spotify(auth=access_token)
            
            # Get current user info
            yield f"data: {json.dumps({'status': 'Autenticando...', 'progress': 5})}\n\n"
            me = sp.current_user()
            if not me or not isinstance(me, dict) or "id" not in me:
                raise RuntimeError("Failed to fetch current user from Spotify")
            
            username = me["id"]
            display_name = me.get("display_name") or username
            print(f"✅ Autenticado como: {display_name} ({username})")
            
            # Fetch playlists
            playlists_rows: List[Dict[str, Any]] = []
            yield f"data: {json.dumps({'status': 'Descargando playlists...', 'progress': 15})}\n\n"
            
            playlists_list = list(paginate(sp.current_user_playlists))
            
            for i, pl in enumerate(playlists_list):
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
                progress = 15 + int((i / max(1, len(playlists_list))) * 15)
                yield f"data: {json.dumps({'status': f'Descargando playlist {i+1}/{len(playlists_list)}...', 'progress': progress})}\n\n"
            
            # Fetch liked tracks
            yield f"data: {json.dumps({'status': 'Descargando canciones que te gustan...', 'progress': 35})}\n\n"
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
            
            # Prepare track headers and data
            track_headers = [
                "playlist_id","playlist_name","playlist_owner_id",
                "added_at","added_by_id",
                "track_id","track_isrc","track_uri","track_url",
                "track_name","track_popularity","artists",
                "album_name","album_upc","album_release_date","duration_ms",
                "explicit","is_local"
            ]
            
            tracks_data: List[List[str]] = [track_headers]
            yield f"data: {json.dumps({'status': 'Descargando canciones por playlist...', 'progress': 50})}\n\n"
            
            # Process real playlists
            total_playlists = len([p for p in playlists_rows if p["playlist_id"] != liked_pid])
            processed = 0
            
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
                    
                    if not t or t.get("type") != "track":  # type: ignore
                        continue
                    
                    row = [
                        pid, pname, owner_id,
                        added_at, added_by_id or "",
                        t.get("id") or "",  # type: ignore
                        safe_get_nested(t, "external_ids", "isrc") or "",  # type: ignore
                        t.get("uri") or "",  # type: ignore
                        safe_get_nested(t, "external_urls", "spotify") or "",  # type: ignore
                        t.get("name") or "",  # type: ignore
                        str(t.get("popularity") or ""),  # type: ignore
                        track_artists_str(t),  # type: ignore
                        safe_get_nested(t, "album", "name") or "",  # type: ignore
                        safe_get_nested(t, "album", "external_ids", "upc") or "",  # type: ignore
                        safe_get_nested(t, "album", "release_date") or "",  # type: ignore
                        str(t.get("duration_ms") or ""),  # type: ignore
                        str(t.get("explicit") or ""),  # type: ignore
                        str(is_local)
                    ]
                    tracks_data.append(row)
                
                processed += 1
                progress = 50 + int((processed / max(1, total_playlists)) * 35)
                yield f"data: {json.dumps({'status': f'Procesando: {pname} ({processed}/{total_playlists})', 'progress': progress})}\n\n"
            
            # Process liked tracks
            yield f"data: {json.dumps({'status': 'Agregando canciones que te gustan...', 'progress': 85})}\n\n"
            for item in liked_items:
                added_at = item.get("added_at")
                t: Optional[Dict[str, Any]] = item.get("track")
                if not t:  # type: ignore
                    continue
                
                row = [
                    liked_pid, liked_pname, liked_owner,
                    added_at, None or "",
                    t.get("id") or "",  # type: ignore
                    safe_get_nested(t, "external_ids", "isrc") or "",  # type: ignore
                    t.get("uri") or "",  # type: ignore
                    safe_get_nested(t, "external_urls", "spotify") or "",  # type: ignore
                    t.get("name") or "",  # type: ignore
                    str(t.get("popularity") or ""),  # type: ignore
                    track_artists_str(t),  # type: ignore
                    safe_get_nested(t, "album", "name") or "",  # type: ignore
                    safe_get_nested(t, "album", "external_ids", "upc") or "",  # type: ignore
                    safe_get_nested(t, "album", "release_date") or "",  # type: ignore
                    str(t.get("duration_ms") or ""),  # type: ignore
                    str(t.get("explicit") or ""),  # type: ignore
                    str(False)
                ]
                tracks_data.append(row)
            
            # Finalize
            yield f"data: {json.dumps({'status': 'Finalizando...', 'progress': 95})}\n\n"
            
            # Prepare playlists data for export
            playlists_export = []
            for pl in playlists_rows:
                playlists_export.append([
                    pl["playlist_id"],
                    pl["name"],
                    pl["public"],
                    pl["collaborative"],
                    pl["owner_id"],
                    pl["owner_name"],
                    pl["tracks_total"],
                    pl["href"] or "",
                    pl["external_url"] or "",
                    pl["snapshot_id"] or ""
                ])
            
            playlists_headers = [
                "playlist_id", "name", "public", "collaborative",
                "owner_id", "owner_name", "tracks_total", "href",
                "external_url", "snapshot_id"
            ]
            
            yield f"data: {json.dumps({'status': '✅ Completado', 'progress': 100, 'playlists': playlists_export, 'playlists_headers': playlists_headers, 'tracks': tracks_data})}\n\n"
            
        except Exception as e:
            print(f"Error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e), 'progress': 0})}\n\n"
    
    return Response(
        stream_with_context(generate_progress()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )
