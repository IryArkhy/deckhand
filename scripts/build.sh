#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0")}"
DIST_DIR="dist"
APP_NAME="Deckhand"
ZIP_NAME="${APP_NAME}-${VERSION}.zip"

echo "Building ${APP_NAME} ${VERSION}..."

# Build the .app bundle
pip install pyinstaller
pyinstaller \
  --name "${APP_NAME}" \
  --windowed \
  --onedir \
  --noconfirm \
  deckhand/__main__.py

APP_PATH="${DIST_DIR}/${APP_NAME}.app"

# Ad-hoc sign so Gatekeeper doesn't block unsigned apps
echo "Signing ${APP_NAME}.app (ad-hoc)..."
codesign --force --deep --sign - "${APP_PATH}"

# Zip using ditto (preserves macOS metadata / resource forks)
echo "Creating ${ZIP_NAME}..."
rm -f "${ZIP_NAME}"
ditto -c -k --keepParent "${APP_PATH}" "${ZIP_NAME}"

echo ""
echo "Done: ${ZIP_NAME}"
echo ""
echo "To create a GitHub release:"
echo "  gh release create ${VERSION} ${ZIP_NAME} --title \"${APP_NAME} ${VERSION}\" --notes \"See CHANGELOG\""
