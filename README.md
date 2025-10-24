# Spotify Playlist Compiler

Una aplicación web elegante para descargar tus playlists de Spotify en formato CSV, sin necesidad de almacenar tokens localmente.

## 🎯 Características

- **Autenticación OAuth2 segura** con Spotify
- **Sin almacenamiento local** de tokens (sesión en memoria)
- **Barra de progreso en tiempo real** mediante Server-Sent Events
- **Descarga directa al navegador** en formato CSV
- **Interfaz responsiva** con animaciones fluidas
- Incluye playlists y "Canciones que te gustan"

## 🔐 Flujo de Autenticación

```
1. Usuario hace clic en "Connect to Spotify"
   ↓
2. Se genera un state token (CSRF protection)
   ↓
3. Se redirige a Spotify para autorizar
   ↓
4. Spotify devuelve código de autorización
   ↓
5. Aplicación intercambia código por access token
   ↓
6. Token se almacena en sesión Flask (en memoria, no en disco)
   ↓
7. Usuario autenticado puede descargar datos
```

**Seguridad:**
- ✅ Tokens en memoria (no en archivos)
- ✅ CSRF protection con state tokens
- ✅ Uso de refresh tokens para renovación
- ✅ Sesión segura con SECRET_KEY

## 📁 Estructura del Proyecto

```
.
├── backend/                          # API y lógica del servidor
│   ├── app.py                       # Aplicación Flask
│   ├── config.py                    # Configuración (env vars)
│   ├── auth.py                      # Gestión OAuth2
│   ├── routes.py                    # Endpoints API
│   └── services/
│       ├── __init__.py
│       └── playlist_compilator.py   # Exportación de Spotify
│
├── frontend/                         # Interfaz web
│   ├── index.html                   # Estructura HTML
│   ├── script.js                    # Lógica del cliente
│   └── styles.css                   # Estilos (Spotify theme)
│
├── run.py                           # Punto de entrada
├── requirements.txt                 # Dependencias Python
└── .env                             # Variables de configuración
```

## 🚀 Guía de Inicio

### Requisitos
- Python 3.9+
- Cuenta de Spotify (desarrollador)

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repo-url>
cd spoti-frontend
```

2. **Crear ambiente virtual**
```bash
python -m venv .venv
source .venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno** (`.env`)
```env
DEBUG=False
HOST=0.0.0.0
PORT=8000
SECRET_KEY=tu-clave-secreta-aqui

SPOTIPY_CLIENT_ID=tu-client-id
SPOTIPY_CLIENT_SECRET=tu-client-secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8000/callback
```

### Ejecutar

```bash
python run.py
```

Luego accede a `http://127.0.0.1:8000` en tu navegador.

## 📊 Endpoints API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/auth/login` | GET | Inicia sesión con Spotify |
| `/api/auth/callback` | GET | Callback de Spotify (redirect) |
| `/api/auth/status` | GET | Verifica si está autenticado |
| `/api/auth/logout` | POST | Cierra sesión |
| `/api/export/progress` | GET | Descarga con barra de progreso (SSE) |

## 🎨 Interfaz

- **Tema Spotify**: Verde (#1DB954) y negro (#191414)
- **Animaciones fluidas**: Progress bar con shimmer effect
- **Responsive**: Funciona en desktop y móvil
- **Footer discreto**: Crédito del desarrollador

## 📦 Dependencias Principales

- **Flask**: Framework web
- **Spotipy**: Cliente oficial de Spotify API
- **Flask-CORS**: Soporte CORS
- **python-dotenv**: Gestión de variables de entorno

## � Flujo de Descarga

1. Usuario hace clic en "Download Playlists"
2. Se abre conexión SSE a `/api/export/progress`
3. Backend recopila playlists y canciones en tiempo real
4. Frontend actualiza barra de progreso cada 5-10 segundos
5. Al completar (100%), se generan dos CSV:
   - `playlists_YYYY-MM-DD.csv`
   - `tracks_YYYY-MM-DD.csv`
6. Archivos se descargan automáticamente al navegador

## ⚙️ Configuración Spotify

1. Ve a [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Crea una nueva aplicación
3. Acepta los términos y configura
4. Copia `Client ID` y `Client Secret`
5. Configura Redirect URI: `http://127.0.0.1:8000/callback`
6. Agrega valores a `.env`

## 📝 Notas

- Los tokens no se guardan en disco
- La sesión expira cuando cierras el navegador
- Máximo 50 items por página en la API de Spotify
- Reintento automático en rate limiting (429)

## 👨‍💻 Desarrollado por

**Antonio Trapote** ®
