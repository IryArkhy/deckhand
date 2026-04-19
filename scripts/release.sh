#!/usr/bin/env bash
# Usage: bash scripts/release.sh v0.2.0 "What's new in this version"
set -euo pipefail

VERSION="${1:?Usage: release.sh <version> <notes>}"
NOTES="${2:?Usage: release.sh <version> <notes>}"
APP_NAME="Deckhand"
ZIP_NAME="${APP_NAME}-${VERSION}.zip"
APPCAST="appcast.xml"

SPARKLE_CACHE="/tmp/Sparkle-2.9.1"
SIGN_UPDATE="${SPARKLE_CACHE}/bin/sign_update"

if [ ! -f "${ZIP_NAME}" ]; then
  echo "Error: ${ZIP_NAME} not found. Run scripts/build.sh ${VERSION} first."
  exit 1
fi

# --- Sign the zip and capture signature + length ---
echo "Signing ${ZIP_NAME}..."
SIGN_OUTPUT=$("${SIGN_UPDATE}" "${ZIP_NAME}")
ED_SIG=$(echo "${SIGN_OUTPUT}" | grep -o 'sparkle:edSignature="[^"]*"' | cut -d'"' -f2)
LENGTH=$(echo "${SIGN_OUTPUT}" | grep -o 'length="[^"]*"' | cut -d'"' -f2)
PUB_DATE=$(date -u "+%a, %d %b %Y %H:%M:%S +0000")
DOWNLOAD_URL="https://github.com/IryArkhy/deckhand/releases/download/${VERSION}/${ZIP_NAME}"

echo "  Signature: ${ED_SIG:0:20}..."
echo "  Length:    ${LENGTH}"

# --- Prepend new item to appcast.xml ---
echo "Updating ${APPCAST}..."
ITEM=$(cat <<XMLEOF
    <item>
      <title>Version ${VERSION#v}</title>
      <sparkle:version>${VERSION#v}</sparkle:version>
      <sparkle:shortVersionString>${VERSION#v}</sparkle:shortVersionString>
      <pubDate>${PUB_DATE}</pubDate>
      <sparkle:minimumSystemVersion>12.0</sparkle:minimumSystemVersion>
      <description><![CDATA[${NOTES}]]></description>
      <enclosure
        url="${DOWNLOAD_URL}"
        sparkle:version="${VERSION#v}"
        sparkle:shortVersionString="${VERSION#v}"
        length="${LENGTH}"
        type="application/octet-stream"
        sparkle:edSignature="${ED_SIG}"/>
    </item>
XMLEOF
)

# Insert the new item after the <language> line
python3 - "${APPCAST}" "${ITEM}" <<'PYEOF'
import sys
path, item = sys.argv[1], sys.argv[2]
content = open(path).read()
# Insert new item just before the first existing <item> (or before </channel>)
marker = "    <item>" if "    <item>" in content else "  </channel>"
content = content.replace(marker, item + "\n" + marker, 1)
open(path, "w").write(content)
PYEOF

echo "Updated ${APPCAST}"

# --- Commit and push appcast ---
git add "${APPCAST}"
git commit -m "release: update appcast for ${VERSION}"
git push

# --- Create GitHub release ---
echo "Creating GitHub release ${VERSION}..."
gh release create "${VERSION}" "${ZIP_NAME}" \
  --title "${APP_NAME} ${VERSION}" \
  --notes "${NOTES}"

echo ""
echo "Released: https://github.com/IryArkhy/deckhand/releases/tag/${VERSION}"
