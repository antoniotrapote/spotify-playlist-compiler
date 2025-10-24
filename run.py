#!/usr/bin/env python
"""Run the Spotify Playlist Compiler application."""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.config import DEBUG, HOST, PORT

if __name__ == "__main__":
    app = create_app()
    print(f"\n🎵 Spotify Playlist Compiler")
    print(f"🌐 Server running at http://{HOST}:{PORT}")
    print(f"📁 Debug mode: {DEBUG}\n")
    app.run(debug=DEBUG, host=HOST, port=PORT)
