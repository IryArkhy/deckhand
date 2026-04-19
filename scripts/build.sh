#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0")}"
DIST_DIR="dist"
APP_NAME="Deckhand"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"
ZIP_NAME="${APP_NAME}-${VERSION}.zip"

SPARKLE_VERSION="2.9.1"
SPARKLE_CACHE="/tmp/Sparkle-${SPARKLE_VERSION}"
SPARKLE_FRAMEWORK="${SPARKLE_CACHE}/Sparkle.framework"
SPARKLE_BIN="${SPARKLE_CACHE}/bin"

FEED_URL="https://raw.githubusercontent.com/IryArkhy/deckhand/main/appcast.xml"
PUBLIC_ED_KEY="Vd7IO8f84jmFnhc3kYWJy2wL2n0UDNfO8jl/x0A4r1k="

echo "Building ${APP_NAME} ${VERSION}..."

# --- Download Sparkle if not cached ---
if [ ! -d "${SPARKLE_FRAMEWORK}" ]; then
  echo "Downloading Sparkle ${SPARKLE_VERSION}..."
  curl -L "https://github.com/sparkle-project/Sparkle/releases/download/${SPARKLE_VERSION}/Sparkle-${SPARKLE_VERSION}.tar.xz" \
    -o /tmp/Sparkle.tar.xz
  mkdir -p "${SPARKLE_CACHE}"
  tar -xf /tmp/Sparkle.tar.xz -C "${SPARKLE_CACHE}"
fi

# --- Build the .app bundle ---
pip install pyinstaller
pyinstaller \
  --name "${APP_NAME}" \
  --windowed \
  --onedir \
  --noconfirm \
  deckhand/__main__.py

# --- Bundle Sparkle.framework ---
echo "Bundling Sparkle.framework..."
mkdir -p "${APP_PATH}/Contents/Frameworks"
cp -R "${SPARKLE_FRAMEWORK}" "${APP_PATH}/Contents/Frameworks/"

# --- Patch Info.plist with Sparkle keys ---
echo "Patching Info.plist..."
PLIST="${APP_PATH}/Contents/Info.plist"
plist_set() {
  /usr/libexec/PlistBuddy -c "Set :$1 $2" "${PLIST}" 2>/dev/null || \
  /usr/libexec/PlistBuddy -c "Add :$1 string $2" "${PLIST}"
}
plist_set "SUFeedURL" "${FEED_URL}"
plist_set "SUPublicEDKey" "${PUBLIC_ED_KEY}"
plist_set "CFBundleShortVersionString" "${VERSION#v}"
plist_set "CFBundleVersion" "${VERSION#v}"

# --- Ad-hoc sign everything (framework first, then app) ---
echo "Signing..."
codesign --force --deep --sign - "${APP_PATH}/Contents/Frameworks/Sparkle.framework"
codesign --force --deep --sign - "${APP_PATH}"

# --- Zip using ditto (preserves macOS metadata) ---
echo "Creating ${ZIP_NAME}..."
rm -f "${ZIP_NAME}"
ditto -c -k --keepParent "${APP_PATH}" "${ZIP_NAME}"

echo ""
echo "Done: ${ZIP_NAME} ($(du -sh "${ZIP_NAME}" | cut -f1))"
echo ""
echo "Next: bash scripts/release.sh ${VERSION} \"Release notes here\""
