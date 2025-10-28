# Spotify Playlist Compiler
[![CC BY-NC-SA 4.0](https://licensebuttons.net/l/by-nc-sa/4.0/80x15.png)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

Web application to download your Spotify playlists in CSV format. Including OAuth2 authentication to manage your data securely without storing tokens locally.


## 🎯 Features

- **Secure OAuth2 authentication** with Spotify
- **No local token storage** (in-memory session)
- **Real-time progress bar** via Server-Sent Events
- **Direct browser download** in CSV format
- **Responsive interface** with smooth animations
- Includes playlists and "Liked Tracks"

## 🔐 Authentication Flow

```
1. User clicks "Connect to Spotify"
2. A state token is generated (CSRF protection)
3. Redirected to Spotify for authorization
4. Spotify returns authorization code
5. Application exchanges code for access token
6. Token is stored in Flask session (in-memory, not on disk)
7. Authenticated user can download data
```

More details in [AUTHENTICATION.md](./AUTHENTICATION.md)

**Security:**
- ✅ Tokens in memory (not in files)
- ✅ CSRF protection with state tokens
- ✅ Refresh tokens for token renewal
- ✅ Secure session with SECRET_KEY

## 📁 Project Structure

```
.
├── backend/                          # API and server logic
│   ├── app.py                       # Flask application
│   ├── config.py                    # Configuration (env vars)
│   ├── auth.py                      # OAuth2 management
│   ├── routes.py                    # API endpoints
│   └── services/
│       ├── __init__.py
│       └── playlist_compilator.py   # Spotify export logic
│
├── frontend/                        # Web interface
│   ├── index.html                   # HTML structure
│   ├── script.js                    # Client logic
│   └── styles.css                   # Styles (Spotify theme)
│
├── run.py                           # Entry point
├── requirements.txt                 # Python dependencies
└── .env                             # Configuration variables
```

## 🚀 Getting Started

### Requirements
- Python 3.9+
- Spotify Developer Account

### Installation

1. **Clone the repository**
```bash
git clone <repo-url>
cd spoti-frontend
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables** (`.env`)
```env
DEBUG=False
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your-secret-key-here

SPOTIPY_CLIENT_ID=your-client-id
SPOTIPY_CLIENT_SECRET=your-client-secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8000/callback
```

### Run

```bash
python run.py
```

Then access `http://127.0.0.1:8000` in your browser.

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | GET | Start Spotify login |
| `/api/auth/callback` | GET | Spotify callback (redirect) |
| `/api/auth/status` | GET | Check if authenticated |
| `/api/auth/logout` | POST | Logout |
| `/api/export/progress` | GET | Download with progress bar (SSE) |

## 🎨 Interface

- **Spotify Theme**: Green (#1DB954) and black (#191414)
- **Smooth Animations**: Progress bar with shimmer effect
- **Responsive**: Works on desktop and mobile
- **Discrete Footer**: Developer credit

## 📦 Main Dependencies

- **Flask**: Web framework
- **Spotipy**: Official Spotify API client
- **Flask-CORS**: CORS support
- **python-dotenv**: Environment variable management

## 🔄 Download Flow

1. User clicks "Download Playlists"
2. SSE connection opens to `/api/export/progress`
3. Backend collects playlists and tracks in real-time
4. Frontend updates progress bar every 5-10 seconds
5. On completion (100%), two CSV files are generated:
   - `playlists_YYYY-MM-DD.csv`
   - `tracks_YYYY-MM-DD.csv`
6. Files automatically download to browser

## ⚙️ Spotify Configuration

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Accept terms and configure
4. Copy `Client ID` and `Client Secret`
5. Set Redirect URI: `http://127.0.0.1:8000/callback`
6. Add values to `.env`

## 📝 Notes

- Tokens are not saved to disk
- Session expires when you close the browser
- Maximum 50 items per page in Spotify API
- Automatic retry on rate limiting (429)


## ⚖️ License

CC BY-NC-SA 4.0 &copy; 2025 [Antonio L. Martínez Trapote](https://github.com/antoniotrapote) 

[![CC BY-NC-SA 4.0](https://licensebuttons.net/l/by-nc-sa/4.0/80x15.png)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
