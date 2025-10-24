"""Flask application to serve the Spotify Playlist Compiler."""

from flask import Flask, send_from_directory, redirect, request
from flask_cors import CORS
from pathlib import Path
from urllib.parse import urlencode
from backend.config import FRONTEND_DIR, DEBUG, HOST, PORT, SECRET_KEY
from backend.routes import api

# Allowed file extensions for static files
ALLOWED_EXTENSIONS = {".html", ".css", ".js", ".json", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf"}


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    CORS(app, supports_credentials=True)
    
    # Register blueprints
    app.register_blueprint(api)
    
    # Redirect /callback to /api/auth/callback for Spotify OAuth
    @app.route("/callback")
    def callback_redirect():
        """Redirect old callback URL to new API endpoint."""
        # Forward all query parameters
        args = dict(request.args)
        return redirect(f"/api/auth/callback?{urlencode(args)}")
    
    # Serve frontend
    @app.route("/")
    def index():
        """Serve the main HTML file."""
        return send_from_directory(FRONTEND_DIR, "index.html")
    
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        """Serve static files from the frontend folder."""
        # Security checks
        frontend_path = Path(FRONTEND_DIR).resolve() / path
        
        try:
            # Prevent directory traversal attacks
            frontend_path.relative_to(Path(FRONTEND_DIR).resolve())
        except ValueError:
            # Path is outside frontend directory
            return "Not found", 404
        
        # Only serve files with allowed extensions
        if frontend_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            return "Not found", 404
        
        # Check if file exists
        if frontend_path.is_file():
            return send_from_directory(FRONTEND_DIR, path)
        
        return "Not found", 404
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=DEBUG, host=HOST, port=PORT)
