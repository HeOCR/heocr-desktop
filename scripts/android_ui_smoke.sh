#!/bin/bash
# Start the plain (non-test) APK in the CI emulator, press "Try a sample", and check the app is
# still alive after reading it; save a screenshot and the app's log lines.
#   scripts/android_ui_smoke.sh dist/HeOCR-android-arm64-debug.apk
set -euo pipefail
APK="$1"
SDK=~/.cache/briefcase/tools/android_sdk
ADB="$SDK/platform-tools/adb"
PKG=io.github.heocr.heocr_mobile
mkdir -p dist/ui-smoke
"$SDK/emulator/emulator" -avd heocrPhone -no-window -no-snapshot -no-audio -no-boot-anim > dist/ui-smoke/emulator.log 2>&1 &
"$ADB" wait-for-device
until [ "$("$ADB" shell getprop sys.boot_completed | tr -d '\r')" = "1" ]; do sleep 5; done
"$ADB" install -r "$APK"
"$ADB" logcat -c
"$ADB" shell am start -n "$PKG/org.beeware.android.MainActivity"
alive() { "$ADB" shell pidof "$PKG" >/dev/null; }
fail() { echo "$1"; "$ADB" logcat -d > dist/ui-smoke/logcat.txt; grep -E "AndroidRuntime|python\.std" dist/ui-smoke/logcat.txt | tail -60; exit 1; }
sleep 45
alive || fail "the app is not running after start"
"$ADB" exec-out screencap -p > dist/ui-smoke/1-start.png
"$ADB" shell uiautomator dump /sdcard/ui.xml >/dev/null && "$ADB" pull -q /sdcard/ui.xml dist/ui-smoke/ui.xml
POS=$(python3 - dist/ui-smoke/ui.xml <<'PY'
import re, sys
xml = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'text="try a sample"[^>]*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml, re.I)
print(f"{(int(m[1]) + int(m[3])) // 2} {(int(m[2]) + int(m[4])) // 2}" if m else "")
PY
)
[ -n "$POS" ] || fail "no 'Try a sample' button on screen"
"$ADB" shell input tap $POS
for _ in $(seq 1 24); do
  sleep 5
  alive || fail "the app stopped while reading the sample"
  "$ADB" shell uiautomator dump /sdcard/ui.xml >/dev/null && "$ADB" pull -q /sdcard/ui.xml dist/ui-smoke/ui-after.xml
  if grep -Eq 'text="[0-9.]+ s"' dist/ui-smoke/ui-after.xml; then break; fi
done
"$ADB" exec-out screencap -p > dist/ui-smoke/2-sample.png
"$ADB" logcat -d > dist/ui-smoke/logcat.txt
grep -Eq 'text="[0-9.]+ s"' dist/ui-smoke/ui-after.xml || fail "the sample was not read within 2 minutes"
grep -o 'text="[0-9.]* s"' dist/ui-smoke/ui-after.xml
echo "UI smoke passed: started, read the sample, still running"
