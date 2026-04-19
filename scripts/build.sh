#!/usr/bin/env bash
set -euo pipefail

echo "Installing PyInstaller..."
pip install pyinstaller

echo "Building Deckhand.app..."
pyinstaller \
  --name "Deckhand" \
  --windowed \
  --onedir \
  --noconfirm \
  deckhand/__main__.py

echo ""
echo "Done. App bundle at: dist/Deckhand.app"
echo "To distribute: zip -r Deckhand.zip dist/Deckhand.app"
