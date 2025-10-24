# Spotify Playlist Compiler

An application to export your Spotify playlists to CSV files.

This project compiles all your playlists and tracks from Spotify into easily accessible CSV files, allowing you to:
- Export all your playlists with metadata (name, owner, track count, etc.)
- Export all tracks from your playlists with detailed information (artist, album, duration, explicit flag, etc.)
- Manage multiple user accounts with separate cache files
- Handle API rate limiting gracefully

---

## Features

- 🔐 Secure Spotify OAuth authentication
- 📊 Exports playlists to CSV format
- 🎵 Exports all tracks with comprehensive metadata
- 👥 Multi-user support with dedicated cache files
- ⚡ Rate limiting and retry logic for API calls
- 🛡️ Safe nested dictionary access for robust data extraction

---

## Setup



---

## 📁 Structure

```
.github/               # Copilot and instructions files
.vscode/               # VSCode settings and extensions
.caches/               # User authentication cache files
.gitignore             # Excludes .venv, .env, and temporary files
AGENTS.md              # AI assistant documentation
LICENSE                # MIT License
README.md              # This file
requirements.txt       # Project dependencies
research.ipynb         # Development notebook with export logic
export_spotify.py      # Main export script
```

---

## 🚀 Usage

### Requirements
- Python 3.10+
- Spotify Developer Account ([register here](https://developer.spotify.com/dashboard))

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Spotify credentials:
   ```
   SPOTIPY_CLIENT_ID=your_client_id
   SPOTIPY_CLIENT_SECRET=your_client_secret
   SPOTIPY_REDIRECT_URI=http://127.0.0.1:8000/callback
   ```

### Running the Export

Execute the script to export your playlists and tracks:
```bash
python export_spotify.py
```

Or use the Jupyter notebook in VS Code:
```bash
research.ipynb
```

This will generate two CSV files:
- `playlists_<username>.csv` - All playlists with metadata
- `tracks_<username>.csv` - All tracks from all playlists with detailed information

---

## 📄 Output Files

### Playlists CSV
- `playlist_id`, `name`, `public`, `collaborative`, `owner_id`, `owner_name`, `tracks_total`, `href`, `external_url`, `snapshot_id`

### Tracks CSV
---

## 🔧 Configuration

- **Cache Directory**: `.caches/` - Stores user-specific authentication tokens
- **Environment Variables**: Load from `.env` file via `python-dotenv`
- **Rate Limiting**: Implements exponential backoff for API rate limit (429) responses

---

## 📦 Dependencies

- `spotipy` - Spotify Web API client
- `python-dotenv` - Environment variable management
- `ipykernel` - Jupyter kernel for notebook support

---

## ⚖️ License

MIT © Antonio L. Martínez Trapote
