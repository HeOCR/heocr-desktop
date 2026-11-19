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
#   5. notarizes and staples the app, then the DMG, only if `xcrun notarytool history --keychain-profile heocr-notary`
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
VERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1)
# Always a fresh app: `briefcase update` keeps the Info.plist written at create time, so a
# version bump would not reach CFBundleShortVersionString. The old build goes to the Trash.
if [ -d build/heocr_desktop/macos ]; then
  trash build/heocr_desktop/macos
fi
briefcase create macOS -a heocr_desktop --no-input
briefcase build macOS -a heocr_desktop --no-input
PLIST_VERSION=$(/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$APP/Contents/Info.plist")
[ "$PLIST_VERSION" = "$VERSION" ] || { echo "Info.plist says $PLIST_VERSION, pyproject.toml says $VERSION"; exit 1; }

# Sign the app bundle (Briefcase signs nested binaries inside-out, with --options runtime).
briefcase package macOS -a heocr_desktop --identity "$IDENTITY" --no-notarize --no-input
codesign --verify --deep --strict --verbose=2 "$APP"
codesign -d --entitlements - --xml "$APP" >/dev/null
TESS="$APP/Contents/Resources/app/heocr_desktop/resources/tesseract/tesseract"
codesign -dv "$TESS" 2>&1 | grep -E "Authority=Developer ID Application|flags=.*runtime" || { echo "tesseract not signed with hardened runtime"; exit 1; }
lipo -info "$TESS"

"$PY" scripts/smoke_app.py macos

BUILT=$(ls -t dist/*.dmg | grep -v -- '-macos.dmg' | head -1)
DMG="dist/HeOCR-${VERSION}-macos.dmg"   # the name the download page links to
WORK="build/notarize"
rm -rf "$WORK" "$DMG"; mkdir -p "$WORK"

if ! xcrun notarytool history --keychain-profile "$PROFILE" >/dev/null 2>&1; then
  cp "$BUILT" "$DMG"
  codesign --verify --verbose=2 "$DMG"
  echo "No notary profile '$PROFILE' yet: the DMG is signed but NOT notarized."
  echo "Gatekeeper will warn on other Macs until it is. Rerun this script once the profile exists."
  shasum -a 256 "$DMG"
  exit 0
fi

# 1. Notarize the app itself and staple its ticket, so it opens offline even when copied out
#    of the DMG (many HeOCR users work without internet; Gatekeeper needs the ticket then).
ditto -c -k --keepParent "$APP" "$WORK/HeOCR-app.zip"
xcrun notarytool submit "$WORK/HeOCR-app.zip" --keychain-profile "$PROFILE" --wait | tee "$WORK/app-notary.txt"
grep -q "status: Accepted" "$WORK/app-notary.txt" || { echo "app notarization not accepted"; exit 1; }
xcrun stapler staple "$APP"
xcrun stapler validate "$APP"

# 2. Put the stapled app into Briefcase's DMG (same layout), without re-signing the app.
hdiutil convert "$BUILT" -format UDRW -o "$WORK/rw.dmg" -quiet
hdiutil resize -size 400m "$WORK/rw.dmg" -quiet
MNT="$WORK/mnt"; mkdir -p "$MNT"
hdiutil attach "$WORK/rw.dmg" -nobrowse -noautoopen -mountpoint "$MNT" -quiet
rm -rf "$MNT/HeOCR.app"
ditto "$APP" "$MNT/HeOCR.app"
xcrun stapler validate "$MNT/HeOCR.app"
hdiutil detach "$MNT" -quiet
hdiutil convert "$WORK/rw.dmg" -format UDZO -imagekey zlib-level=9 -o "$DMG" -quiet

# 3. Sign, notarize and staple the DMG.
codesign --sign "$IDENTITY" --timestamp "$DMG"
codesign --verify --verbose=2 "$DMG"
xcrun notarytool submit "$DMG" --keychain-profile "$PROFILE" --wait | tee "$WORK/dmg-notary.txt"
grep -q "status: Accepted" "$WORK/dmg-notary.txt" || { echo "DMG notarization not accepted"; exit 1; }
xcrun stapler staple "$DMG"
xcrun stapler validate "$DMG"
spctl -a -vv -t exec "$APP"
spctl -a -vv -t open --context context:primary-signature "$DMG"
shasum -a 256 "$DMG"
