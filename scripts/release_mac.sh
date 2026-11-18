#!/bin/bash
# Build, sign and (when the notary profile exists) notarize the macOS DMG, on the maintainer's Mac.
#
#   scripts/release_mac.sh build/tess/macos-arm64 build/tess/macos-x86_64
#
# The two Tesseract folders come from scripts/build_tesseract.py, or from the Tesseract workflow's
# artifacts (tesseract-macos-arm64, tesseract-macos-x86_64). The script:
#   1. bundles Tesseract (universal2) and its models;
#   2. builds the app with Briefcase and signs every binary with the Developer ID Application
#      identity, hardened runtime on (Briefcase does this);
#   3. smoke-tests the signed app on the fixtures;
#   4. builds the DMG and signs it;
#   5. notarizes and staples it, only if `xcrun notarytool history --keychain-profile heocr-notary`
#      works. The maintainer creates that profile himself (`xcrun notarytool store-credentials
#      heocr-notary`); this script never asks for, reads or prints a password.
set -euo pipefail
cd "$(dirname "$0")/.."

IDENTITY="${HEOCR_SIGN_IDENTITY:-Developer ID Application: Shay Palachy Affek (8X657D2YAU)}"
PROFILE="${HEOCR_NOTARY_PROFILE:-heocr-notary}"
PY="${PYTHON:-python3}"
[ $# -eq 2 ] || { echo "usage: $0 <tess-arm64-dir> <tess-x86_64-dir>"; exit 2; }

"$PY" scripts/prebuild_wheels.py
"$PY" scripts/assemble_resources.py "$1" "$2"

APP="build/heocr_desktop/macos/app/HeOCR.app"
if [ -d "$APP" ]; then
  briefcase update macOS --update-requirements --update-resources --no-input
else
  briefcase create macOS --no-input
fi
briefcase build macOS --no-input

# Sign the app bundle (Briefcase signs nested binaries inside-out, with --options runtime).
briefcase package macOS --identity "$IDENTITY" --no-notarize --no-input
codesign --verify --deep --strict --verbose=2 "$APP"
codesign -d --entitlements - --xml "$APP" >/dev/null
TESS="$APP/Contents/Resources/app/heocr_desktop/resources/tesseract/tesseract"
codesign -dv "$TESS" 2>&1 | grep -E "Authority=Developer ID Application|flags=.*runtime" || { echo "tesseract not signed with hardened runtime"; exit 1; }
lipo -info "$TESS"

"$PY" scripts/smoke_app.py macos

VERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1)
BUILT=$(ls -t dist/*.dmg | grep -v -- '-macos.dmg' | head -1)
DMG="dist/HeOCR-${VERSION}-macos.dmg"   # the name the download page links to
cp "$BUILT" "$DMG"
codesign --verify --verbose=2 "$DMG"

if xcrun notarytool history --keychain-profile "$PROFILE" >/dev/null 2>&1; then
  echo "Notarizing $DMG with profile $PROFILE"
  xcrun notarytool submit "$DMG" --keychain-profile "$PROFILE" --wait
  xcrun stapler staple "$DMG"
  xcrun stapler validate "$DMG"
  spctl -a -t open --context context:primary-signature -v "$DMG"
else
  echo "No notary profile '$PROFILE' yet: the DMG is signed but NOT notarized."
  echo "Gatekeeper will warn on other Macs until it is. To notarize later:"
  echo "  xcrun notarytool submit '$DMG' --keychain-profile $PROFILE --wait && xcrun stapler staple '$DMG'"
fi
shasum -a 256 "$DMG"
