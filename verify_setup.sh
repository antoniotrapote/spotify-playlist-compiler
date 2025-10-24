#!/bin/bash
# Verificación rápida de la configuración

echo "🔍 Verificando configuración..."
echo ""

# Check .env exists
if [ -f .env ]; then
    echo "✅ .env existe"
    if grep -q "SPOTIPY_CLIENT_ID" .env; then
        echo "✅ SPOTIPY_CLIENT_ID configurado"
    else
        echo "❌ SPOTIPY_CLIENT_ID no configurado"
    fi
    if grep -q "SPOTIPY_CLIENT_SECRET" .env; then
        echo "✅ SPOTIPY_CLIENT_SECRET configurado"
    else
        echo "❌ SPOTIPY_CLIENT_SECRET no configurado"
    fi
    if grep -q "SPOTIPY_REDIRECT_URI" .env; then
        echo "✅ SPOTIPY_REDIRECT_URI configurado"
    else
        echo "❌ SPOTIPY_REDIRECT_URI no configurado"
    fi
else
    echo "❌ .env NO existe - Necesita ser creado"
fi

echo ""


# Check Python files
echo "🔍 Verificando archivos Python..."
if [ -f "backend/auth.py" ]; then
    echo "✅ backend/auth.py existe"
else
    echo "❌ backend/auth.py NO existe"
fi

if [ -f "backend/routes.py" ]; then
    echo "✅ backend/routes.py existe"
else
    echo "❌ backend/routes.py NO existe"
fi

echo ""

# Check frontend files
echo "🔍 Verificando archivos frontend..."
if [ -f "frontend/index.html" ]; then
    if grep -q "loginSection" frontend/index.html; then
        echo "✅ frontend/index.html tiene loginSection"
    else
        echo "❌ frontend/index.html NO tiene loginSection"
    fi
else
    echo "❌ frontend/index.html NO existe"
fi

if [ -f "frontend/script.js" ]; then
    if grep -q "checkAuthStatus" frontend/script.js; then
        echo "✅ frontend/script.js tiene checkAuthStatus"
    else
        echo "❌ frontend/script.js NO tiene checkAuthStatus"
    fi
else
    echo "❌ frontend/script.js NO existe"
fi

echo ""
echo "✅ Verificación completada"
