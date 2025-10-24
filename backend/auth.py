"""Spotify OAuth2 authentication management."""

import base64
import requests
from urllib.parse import urlencode
from backend.config import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI


def get_auth_url(state: str) -> str:
    """Generate Spotify authorization URL for OAuth2 flow.
    
    Args:
        state: CSRF protection token
        
    Returns:
        Authorization URL
    """
    scopes = [
        "playlist-read-private",
        "playlist-read-collaborative",
        "user-library-read"
    ]
    
    params = {
        "client_id": SPOTIPY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIPY_REDIRECT_URI,
        "scope": " ".join(scopes),
        "state": state
    }
    
    return f"https://accounts.spotify.com/authorize?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access token.
    
    Args:
        code: Authorization code from Spotify
        
    Returns:
        Dict with access_token, token_type, expires_in, refresh_token
    """
    auth_str = f"{SPOTIPY_CLIENT_ID}:{SPOTIPY_CLIENT_SECRET}"
    auth_bytes = auth_str.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
    
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth_b64}"},
        data={
            "code": code,
            "redirect_uri": SPOTIPY_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
    )
    
    response.raise_for_status()
    return response.json()


def refresh_access_token(refresh_token: str) -> dict:
    """Refresh an access token using refresh token.
    
    Args:
        refresh_token: Spotify refresh token
        
    Returns:
        Dict with new access_token and expires_in
    """
    auth_str = f"{SPOTIPY_CLIENT_ID}:{SPOTIPY_CLIENT_SECRET}"
    auth_bytes = auth_str.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
    
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth_b64}"},
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
    )
    
    response.raise_for_status()
    return response.json()
