#!/bin/bash
# Script para crear y configurar repositorio en GitHub

echo "🚀 Configuración de Repositorio GitHub"
echo "======================================"
echo ""

# Información del repositorio
REPO_NAME="skate3-rpcs3-proxy-linux"
REPO_DESC="🎮 Complete Linux port of Skate 3 Online Proxy for RPCS3. EA Blaze protocol implementation with working authentication. 95% functional."

echo "📝 Información del repositorio:"
echo "   Nombre: $REPO_NAME"
echo "   Descripción: $REPO_DESC"
echo ""

# Verificar si gh está instalado
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) no está instalado"
    echo ""
    echo "Opción 1: Instalar gh"
    echo "  sudo pacman -S github-cli  # Arch"
    echo "  gh auth login"
    echo ""
    echo "Opción 2: Manual en web"
    echo "  1. Ir a https://github.com/new"
    echo "  2. Nombre: $REPO_NAME"
    echo "  3. Descripción: $REPO_DESC"
    echo "  4. Público/Privado: Tu elección"
    echo "  5. NO agregar README, .gitignore, license (ya los tenemos)"
    echo "  6. Create repository"
    echo ""
    echo "Luego ejecutar:"
    echo "  cd ~/Escritorio/skate3-proxy-linux"
    echo "  git remote add origin https://github.com/TU_USERNAME/$REPO_NAME.git"
    echo "  git push -u origin main"
    exit 1
fi

# Crear repo con gh
echo "🔨 Creando repositorio..."
echo ""

read -p "¿Repositorio público o privado? (pub/priv): " visibility

if [ "$visibility" = "pub" ]; then
    VISIBILITY="--public"
else
    VISIBILITY="--private"
fi

gh repo create "$REPO_NAME" \
    $VISIBILITY \
    --description "$REPO_DESC" \
    --source=. \
    --remote=origin

echo ""
echo "✅ Repositorio creado!"
echo ""
echo "🚀 Subiendo código..."
git push -u origin main

echo ""
echo "======================================"
echo "✅ ¡COMPLETADO!"
echo "======================================"
echo ""
echo "🌐 Tu repositorio:"
gh repo view --web

echo ""
echo "📊 Próximos pasos opcionales:"
echo "  - Agregar topics: rpcs3, skate3, emulator, proxy, ea-blaze"
echo "  - Crear releases: gh release create v0.95"
echo "  - Enable issues y discussions en Settings"
echo ""
