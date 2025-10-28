# 🔐 Detailed Authentication Flow

This document explains the complete OAuth2 authentication flow used in the Spotify Playlist Compiler.

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Step-by-Step Flow](#step-by-step-flow)
3. [Complete Flow Diagram](#complete-flow-diagram)
4. [Security Features](#security-features)
5. [Token Management](#token-management)
6. [Error Handling](#error-handling)

---

## Initial Setup

Before any user action, the application must be configured with Spotify credentials:

```env
# .env Configuration
SPOTIPY_CLIENT_ID=your_spotify_app_id
SPOTIPY_CLIENT_SECRET=your_spotify_app_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8000/callback
SECRET_KEY=your_flask_session_encryption_key
```

These values are loaded from environment variables in `backend/config.py`:

```python
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
```

---

## Step-by-Step Flow

### Step 1: User Initiates Login

**User Action:** Clicks "Connect to Spotify" button

**Frontend Code** (`frontend/script.js`):
```javascript
loginBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/auth/login');
        const data = await response.json();
        window.location.href = data.auth_url;  // Redirect to Spotify
    } catch (error) {
        console.error('Error:', error);
        statusDiv.textContent = `❌ Error: ${error.message}`;
    }
});
```

**Request:** `GET /api/auth/login`

---

### Step 2: Backend Generates Authorization URL

**Endpoint:** `GET /api/auth/login` in `backend/routes.py`

```python
@api.route("/auth/login", methods=["GET"])
def auth_login():
    """Initiate Spotify OAuth2 login flow."""
    state = secrets.token_urlsafe(32)  # Generate random CSRF token
    session["auth_state"] = state      # Store in Flask session
    auth_url = get_auth_url(state)     # Generate Spotify authorization URL
    return jsonify({"auth_url": auth_url}), 200
```

**Backend Code** (`backend/auth.py`):
```python
def get_auth_url(state: str) -> str:
    """Generate Spotify OAuth2 authorization URL with PKCE."""
    # Generate code verifier for PKCE (Proof Key for Code Exchange)
    code_verifier = ''.join(random.choices(string.ascii_letters + string.digits + '-._~', k=128))
    session['code_verifier'] = code_verifier
    
    # Create code challenge from verifier
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    # Build authorization URL
    auth_url = f"{SPOTIFY_AUTH_URL}?" + urlencode({
        "client_id": SPOTIPY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIPY_REDIRECT_URI,
        "scope": "playlist-read-private playlist-read-collaborative user-library-read",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    })
    return auth_url
```

**Result:** Returns JSON with Spotify authorization URL:
```json
{
    "auth_url": "https://accounts.spotify.com/authorize?client_id=...&state=...&code_challenge=..."
}
```

---

### Step 3: User Authenticates with Spotify

**What Happens:**
1. Browser redirects to Spotify's authorization endpoint
2. User logs into Spotify (if not already logged in)
3. User sees consent screen with requested permissions:
   - Access to private playlists
   - Access to collaborative playlists
   - Access to saved tracks (liked songs)
4. User clicks "Allow" or "Deny"

**Spotify Authorization URL Format:**
```
https://accounts.spotify.com/authorize?
  client_id=YOUR_CLIENT_ID&
  response_type=code&
  redirect_uri=http://127.0.0.1:8000/callback&
  scope=playlist-read-private+playlist-read-collaborative+user-library-read&
  state=random_csrf_token_32_chars&
  code_challenge=pkce_challenge_hash&
  code_challenge_method=S256
```

---

### Step 4: Spotify Redirects Back to Your App

**If User Allows:**
```
http://127.0.0.1:8000/callback?
  code=AQD7I1YdZ...&
  state=random_csrf_token
```

**If User Denies:**
```
http://127.0.0.1:8000/callback?
  error=access_denied
```

---

### Step 5: Backend Verifies State (CSRF Protection)

**Endpoint:** `GET /callback` (also `/api/auth/callback`)

```python
@api.route("/auth/callback", methods=["GET"])
def auth_callback():
    """Handle Spotify OAuth2 callback."""
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    
    # Check for errors from Spotify
    if error:
        return redirect(f"/?error={error}")
    
    # Verify authorization code exists
    if not code:
        return redirect("/?error=no_code")
    
    # ✅ CSRF Protection: Verify state token matches
    if state != session.get("auth_state"):
        return redirect("/?error=invalid_state")
    
    try:
        # Exchange authorization code for access token
        token_data = exchange_code_for_token(code)
        
        # Store token in Flask session (in-memory, not on disk)
        session["access_token"] = token_data["access_token"]
        session["refresh_token"] = token_data.get("refresh_token")
        session["expires_in"] = token_data.get("expires_in", 3600)
        
        return redirect("/")
    except Exception as e:
        return redirect(f"/?error={str(e)}")
```

---

### Step 6: Exchange Authorization Code for Access Token

**Backend Code** (`backend/auth.py`):
```python
def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access token."""
    code_verifier = session.get('code_verifier')
    
    # Prepare request to Spotify token endpoint
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SPOTIPY_REDIRECT_URI,
            "client_id": SPOTIPY_CLIENT_ID,
            "client_secret": SPOTIPY_CLIENT_SECRET,
            "code_verifier": code_verifier  # PKCE verification
        }
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Token exchange failed: {response.text}")
    
    return response.json()
```

**Response from Spotify:**
```json
{
    "access_token": "BQC...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "AQA...",
    "scope": "playlist-read-collaborative playlist-read-private user-library-read"
}
```

**Important:** 
- `access_token`: Used for API requests (valid for ~1 hour)
- `refresh_token`: Used to get a new access_token when the current one expires
- Both tokens are stored **in Flask session (in-memory)**, not on disk

---

### Step 7: User is Now Authenticated

**Session Storage:**
```python
session["access_token"] = "BQC..."      # Used for API calls
session["refresh_token"] = "AQA..."     # Used to refresh token
session["expires_in"] = 3600            # Expiration time in seconds
```

**Frontend Detects Authentication:**
```javascript
async function checkAuthStatus() {
    const response = await fetch('/api/auth/status');
    const data = await response.json();
    
    if (data.authenticated) {
        loginSection.style.display = 'none';
        downloadSection.style.display = 'block';  // Show download button
    }
}
```

**Backend Check:**
```python
@api.route("/auth/status", methods=["GET"])
def auth_status():
    """Check if user is authenticated."""
    is_authenticated = "access_token" in session
    return jsonify({"authenticated": is_authenticated}), 200
```

---

### Step 8: Use Access Token for API Requests

Once authenticated, the backend can use the access token to make requests to Spotify API:

```python
@api.route("/export/progress", methods=["GET"])
def export_with_progress():
    """Stream export progress using authenticated access token."""
    access_token = session.get("access_token")
    
    if not access_token:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Create Spotify client with access token
    sp = Spotify(auth=access_token)
    
    # Now can access user's data
    me = sp.current_user()          # Get current user info
    playlists = sp.current_user_playlists()  # Get user's playlists
    liked_tracks = sp.current_user_saved_tracks()  # Get liked tracks
```

**No caching to disk:**
```python
# Spotipy is configured without cache files
sp = Spotify(auth=access_token)  # auth_manager=None, cache_path=None
```

---

### Step 9: Token Expiration & Refresh

Access tokens expire after ~1 hour. When expired, use the refresh token:

```python
def refresh_access_token() -> str:
    """Refresh access token if expired."""
    refresh_token = session.get('refresh_token')
    expires_in = session.get('expires_in', 0)
    
    # Make request to Spotify token endpoint
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": SPOTIPY_CLIENT_ID,
            "client_secret": SPOTIPY_CLIENT_SECRET
        }
    )
    
    if response.status_code == 200:
        token_info = response.json()
        session['access_token'] = token_info['access_token']
        session['expires_in'] = token_info.get('expires_in', 3600)
        return session['access_token']
    else:
        raise RuntimeError("Token refresh failed")
```

---

### Step 10: Logout

**Frontend:**
```javascript
logoutBtn.addEventListener('click', async () => {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        await checkAuthStatus();  // Update UI
        statusDiv.textContent = '✅ Logged out';
    } catch (error) {
        console.error('Error:', error);
    }
});
```

**Backend:**
```python
@api.route("/auth/logout", methods=["POST"])
def auth_logout():
    """Logout user and clear session tokens."""
    session.clear()  # Remove all session data (access_token, refresh_token, etc.)
    return jsonify({"success": True}), 200
```

---

## Complete Flow Diagram

```
┌──────────┐                    ┌─────────────┐                   ┌──────────┐
│  Browser │                    │ Your Server │                   │ Spotify  │
└──────────┘                    └─────────────┘                   └──────────┘
     │                                │                                 │
     │  1. Click "Connect"            │                                 │
     ├─────────────────────────────>  │                                 │
     │    GET /api/auth/login         │                                 │
     │                                │  2. Generate auth URL           │
     │                                │     (state, code_challenge)     │
     │                                │                                 │
     │  3. Redirect to Spotify        │                                 │
     │    auth_url                    │                                 │
     ├────────────────────────────────────────────────────────────────>│
     │                                │                                 │
     │                         4. User logs in & grants permissions     │
     │                                │                                 │
     │  5. Redirect with code         │                                 │
     │    GET /callback?code=...&state=│                                 │
     |<─────────────────────────────────────────────────────────────────┤
     │                                │                                 │
     │                                │  6. Verify state (CSRF check)   │
     │                                │  7. Verify code_verifier (PKCE) │
     │                                │  8. Exchange code for token     │
     │                                ├─────────────────────────────────>│
     │                                │                                 │
     │                                │  POST /token                    │
     │                                │  grant_type=authorization_code  │
     │                                │  code_verifier=...              │
     │                                │                                 │
     │                                │<─────────────────────────────────┤
     │                                │  {                              │
     │                                │    "access_token": "BQC...",    │
     │                                │    "refresh_token": "AQA...",   │
     │                                │    "expires_in": 3600           │
     │                                │  }                              │
     │                                │                                 │
     │                                │  9. Store in session (memory)   │
     │  10. Redirect to home          │                                 │
     │     GET /                      │                                 │
     |<─────────────────────────────  │                                 │
     │                                │                                 │
     │  11. Frontend: Check auth      │                                 │
     │     GET /api/auth/status       │                                 │
     ├─────────────────────────────>  │                                 │
     │                                │  Returns: {"authenticated": true}
     |<─────────────────────────────  │                                 │
     │                                │                                 │
     │  12. Show download button      │                                 │
     │                                │                                 │
     │  13. User clicks download      │                                 │
     ├─────────────────────────────>  │                                 │
     │    GET /api/export/progress    │                                 │
     │                                │  14. Use access_token           │
     │                                ├─────────────────────────────────>│
     │                                │  GET /v1/me                     │
     │                                │  GET /v1/me/playlists           │
     │                                │  GET /v1/me/tracks              │
     │                                │<─────────────────────────────────┤
     │                                │                                 │
     │  15. Stream progress updates   │                                 │
     │     SSE messages with %        │                                 │
     |<─────────────────────────────  │                                 │
     │                                │                                 │
     │  16. Download CSV files        │                                 │
     │     Browser auto-download      │                                 │
     │                                │                                 │
```

---

## Security Features

| Feature | Purpose | Implementation |
|---------|---------|-----------------|
| **State Token** | CSRF Protection | Random 32-char token stored in session |
| **PKCE** | Authorization Code Interception Prevention | code_challenge in authorization URL |
| **code_verifier** | Verify legitimate code exchange | Sent with token request |
| **Session-Based Storage** | No disk persistence | Flask session (in-memory only) |
| **SECRET_KEY** | Session encryption | `session['access_token']` encrypted |
| **HTTP-Only Cookies** | Prevent XSS token theft | Flask session cookies are HTTP-only |
| **No Token Logging** | Prevent token exposure in logs | Tokens never printed or logged |
| **Scope Limiting** | Minimal permissions | Only request `playlist-read-*` and `user-library-read` |

---

## Token Management

### Storage Locations

| Token | Stored In | Duration | Security |
|-------|-----------|----------|----------|
| `access_token` | Flask session (memory) | ~1 hour | Encrypted in session |
| `refresh_token` | Flask session (memory) | ~1 year | Encrypted in session |
| `state` | Flask session (memory) | 1 request | Encrypted in session |
| `code_verifier` | Flask session (memory) | 1 request | Encrypted in session |

### Token Lifecycle

```
1. User Logs In
   └─> access_token: BQC... (expires in 3600 seconds)
   └─> refresh_token: AQA... (long-lived)

2. User Downloads Data (within 1 hour)
   └─> access_token is valid, use it directly

3. User Waits > 1 hour, Then Downloads
   └─> access_token expired
   └─> Use refresh_token to get new access_token
   └─> Continue with new token

4. User Logs Out
   └─> session.clear() removes all tokens
   └─> Both tokens destroyed from memory
```

---

## Error Handling

### Possible Errors

#### **User Denies Permission**
```
Error: access_denied
Redirect: /?error=access_denied
Frontend: Display error message
```

#### **Missing Authorization Code**
```
Error: no_code
Redirect: /?error=no_code
Frontend: Display error message
```

#### **CSRF Token Mismatch**
```
Error: invalid_state
Redirect: /?error=invalid_state
Frontend: Display error message
Attack Prevented: Malicious redirect detected
```

#### **Token Exchange Failure**
```
Error: Token exchange failed: {...}
Redirect: /?error=Token%20exchange%20failed
Frontend: Display error message
```

#### **API Request without Authentication**
```
Response: {"error": "Not authenticated"}
Status: 401 Unauthorized
Frontend: Redirect to login
```

---

## Implementation Notes

### Why No Disk Storage?

The application stores tokens **only in memory** (Flask session) for security reasons:

1. **No Disk Vulnerabilities:** Can't be exposed via file system access
2. **Session Isolation:** Each user has separate session
3. **Automatic Cleanup:** Tokens cleared on logout or browser close
4. **No Cache Files:** Unlike traditional OAuth apps, we don't cache to `.cache` directory

### Why PKCE?

PKCE (Proof Key for Code Exchange) prevents "authorization code interception attacks":

```python
# Attacker cannot steal the code and exchange it for a token
# because they don't have the code_verifier

# Our implementation:
code_verifier = generate_random_128_char_string()
code_challenge = SHA256(code_verifier)

# Authorization URL includes: code_challenge
# Token request includes: code_verifier (matches challenge)
# Attacker intercepts code but doesn't have verifier → fails
```

### Why Flask Sessions?

```python
session['access_token'] = token  # Encrypted by SECRET_KEY
# vs
open('file.txt', 'w').write(token)  # Plain text on disk
```

Flask sessions are:
- Encrypted with SECRET_KEY
- Signed with HMAC to prevent tampering
- Stored in browser cookie (secure mode)
- Cleared automatically on logout

---

## Testing Authentication Flow

### Manual Test Scenario

1. **Start server:** `python run.py`
2. **Open browser:** `http://127.0.0.1:8000`
3. **Click "Connect to Spotify"**
   - Should redirect to Spotify login
4. **Log in to Spotify**
   - Should show consent screen
5. **Click "Allow"**
   - Should redirect back to application
6. **Verify authenticated:**
   - Download button should appear
   - "Logout" button should appear
7. **Click "Download Playlists"**
   - Should see progress bar with real-time updates
   - Files should download when complete
8. **Click "Logout"**
   - Download button should disappear
   - Login button should reappear

---

## References

- [Spotify Web API Authorization Guide](https://developer.spotify.com/documentation/web-api/tutorials/code-flow)
- [OAuth 2.0 PKCE](https://tools.ietf.org/html/rfc7636)
- [OWASP: Cross-Site Request Forgery (CSRF)](https://owasp.org/www-community/attacks/csrf)
- [Flask Sessions Documentation](https://flask.palletsprojects.com/en/2.3.x/sessions/)
- [Spotipy Documentation](https://spotipy.readthedocs.io/)

---

## ⚖️ License

CC BY-NC-SA 4.0 &copy; 2025 [Antonio L. Martínez Trapote](https://github.com/antoniotrapote) 

[![CC BY-NC-SA 4.0](https://licensebuttons.net/l/by-nc-sa/4.0/80x15.png)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

