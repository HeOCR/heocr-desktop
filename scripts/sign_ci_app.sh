#!/bin/bash
# Sign, notarize and staple a macOS app that CI built, on the maintainer's Mac, without building it here.
#
#   scripts/sign_ci_app.sh heocr-macos-app.tgz [out-dir] [name-suffix]
#
# The tarball is the `heocr-macos-app-unsigned` artifact of the macOS CI job (Briefcase's
# build/heocr_desktop/macos/app folder). Run it from a checkout at the commit CI built. It:
#   1. unpacks the app into build/heocr_desktop/macos (which must not exist yet);
#   2. signs every binary with the Developer ID Application identity, hardened runtime on
#      (`briefcase package --identity`: signing only, no build);
#   3. notarizes and staples the app, puts it into Briefcase's DMG, then signs, notarizes and
#      staples the DMG, as scripts/release_mac.sh does after its own build.
# Signing and notarizing are light: use this when local builds must wait (a gate window). The
# notary profile is the maintainer's (`xcrun notarytool store-credentials heocr-notary`); this
# script never asks for, reads or prints a password.
set -euo pipefail
TGZ="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="${2:-dist}"
SUFFIX="${3:-}"
cd "$(dirname "$0")/.."
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
IDENTITY="${HEOCR_SIGN_IDENTITY:-Developer ID Application: Shay Palachy Affek (8X657D2YAU)}"
PROFILE="${HEOCR_NOTARY_PROFILE:-heocr-notary}"
BRIEFCASE="${BRIEFCASE:-briefcase}"
VERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1)
APP="build/heocr_desktop/macos/app/HeOCR.app"
[ ! -e build/heocr_desktop/macos ] || { echo "build/heocr_desktop/macos exists; move it to the Trash first"; exit 1; }
mkdir -p build/heocr_desktop/macos
tar -xzf "$TGZ" -C build/heocr_desktop/macos
PLIST_VERSION=$(/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$APP/Contents/Info.plist")
[ "$PLIST_VERSION" = "$VERSION" ] || { echo "the app says $PLIST_VERSION, this checkout says $VERSION: check out the commit CI built"; exit 1; }

"$BRIEFCASE" package macOS -a heocr_desktop --identity "$IDENTITY" --no-notarize --no-input
codesign --verify --deep --strict --verbose=2 "$APP"
TESS="$APP/Contents/Resources/app/heocr_desktop/resources/tesseract/tesseract"
codesign -dv "$TESS" 2>&1 | grep -E "Authority=Developer ID Application|flags=.*runtime" || { echo "tesseract not signed with hardened runtime"; exit 1; }

BUILT=$(ls -t dist/*.dmg | head -1)
WORK="build/notarize"; rm -rf "$WORK"; mkdir -p "$WORK"
DMG="$OUT/HeOCR-${VERSION}${SUFFIX}-macos.dmg"
ditto -c -k --keepParent "$APP" "$WORK/HeOCR-app.zip"
xcrun notarytool submit "$WORK/HeOCR-app.zip" --keychain-profile "$PROFILE" --wait | tee "$WORK/app-notary.txt"
grep -q "status: Accepted" "$WORK/app-notary.txt" || { echo "app notarization not accepted"; exit 1; }
xcrun stapler staple "$APP"
xcrun stapler validate "$APP"
hdiutil convert "$BUILT" -format UDRW -o "$WORK/rw.dmg" -quiet
hdiutil resize -size 400m "$WORK/rw.dmg" -quiet
MNT="$WORK/mnt"; mkdir -p "$MNT"
hdiutil attach "$WORK/rw.dmg" -nobrowse -noautoopen -mountpoint "$MNT" -quiet
rm -rf "$MNT/HeOCR.app"
ditto "$APP" "$MNT/HeOCR.app"
xcrun stapler validate "$MNT/HeOCR.app"
hdiutil detach "$MNT" -quiet
rm -f "$DMG"
hdiutil convert "$WORK/rw.dmg" -format UDZO -imagekey zlib-level=9 -o "$DMG" -quiet
codesign --sign "$IDENTITY" --timestamp "$DMG"
codesign --verify --verbose=2 "$DMG"
xcrun notarytool submit "$DMG" --keychain-profile "$PROFILE" --wait | tee "$WORK/dmg-notary.txt"
grep -q "status: Accepted" "$WORK/dmg-notary.txt" || { echo "DMG notarization not accepted"; exit 1; }
xcrun stapler staple "$DMG"
xcrun stapler validate "$DMG"
spctl -a -vv -t exec "$APP"
spctl -a -vv -t open --context context:primary-signature "$DMG"
shasum -a 256 "$DMG"
