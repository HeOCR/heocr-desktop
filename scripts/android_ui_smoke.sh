#!/bin/bash
# Start the plain (non-test) APK in the CI emulator, press "Try a sample", and check the app is
# still alive after reading it; save a screenshot and the app's log lines.
#   scripts/android_ui_smoke.sh dist/HeOCR-android-arm64-debug.apk
set -euo pipefail
APK="$1"
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/.cache/briefcase/tools/android_sdk}}"  # Briefcase uses the runner's SDK when there is one
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
# Find "Try a sample" from the UI tree; uiautomator is flaky on emulators, so fall back to where the
# button sits on a 1080x1920 screen (the first of three equal buttons' middle).
POS=""
for _ in 1 2 3; do
  "$ADB" shell uiautomator dump /data/local/tmp/ui.xml || true
  if "$ADB" pull /data/local/tmp/ui.xml dist/ui-smoke/ui.xml >/dev/null 2>&1; then
    POS=$(python3 - dist/ui-smoke/ui.xml <<'PY'
import re, sys
xml = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'text="try a sample"[^>]*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml, re.I)
print(f"{(int(m[1]) + int(m[3])) // 2} {(int(m[2]) + int(m[4])) // 2}" if m else "")
PY
)
    [ -n "$POS" ] && break
  fi
  sleep 3
done
if [ -z "$POS" ]; then
  SIZE=$("$ADB" shell wm size | grep -o '[0-9]*x[0-9]*' | tail -1)
  W=${SIZE%x*}; H=${SIZE#*x}
  POS="$((W / 2)) $((H * 283 / 1920))"
  echo "uiautomator gave no tree; tapping the button's usual place: $POS"
fi
"$ADB" shell input tap $POS
for _ in $(seq 1 30); do
  sleep 5
  alive || fail "the app stopped while reading the sample"
  if "$ADB" logcat -d | grep -q "HeOCR read sample.png"; then break; fi
done
"$ADB" exec-out screencap -p > dist/ui-smoke/2-sample.png
"$ADB" logcat -d > dist/ui-smoke/logcat.txt
LINE=$(grep -o "HeOCR read sample.png: .*" dist/ui-smoke/logcat.txt | tail -1)
[ -n "$LINE" ] || fail "the sample was not read within 150 seconds"
echo "$LINE"
case "$LINE" in *": ok "*) ;; *) fail "the sample did not read as ok";; esac
alive || fail "the app stopped after reading the sample"
echo "UI smoke passed: started, read the sample, still running"
