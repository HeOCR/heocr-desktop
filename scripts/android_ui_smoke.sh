#!/bin/bash
# Start the plain (non-test) APK in the CI emulator, press "Try a sample", then share a PDF to it from
# "another app" (adb), and check each reading and that the app is still alive; keep screenshots and log.
#   scripts/android_ui_smoke.sh dist/HeOCR-android-arm64-debug.apk
set -euo pipefail
APK="$1"
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/.cache/briefcase/tools/android_sdk}}"  # Briefcase uses the runner's SDK when there is one
ADB="$SDK/platform-tools/adb"
PKG=io.github.heocr.heocr_mobile
mkdir -p "dist/ui-smoke${AVD_SUFFIX:-}"
AVD="${AVD:-heocrPhone}"
OUT="dist/ui-smoke${AVD_SUFFIX:-}"
"$SDK/emulator/emulator" -avd "$AVD" -no-window -no-snapshot -no-audio -no-boot-anim > "dist/ui-smoke-emulator-$AVD.log" 2>&1 &
trap '"$ADB" emu kill >/dev/null 2>&1 || true' EXIT  # one emulator at a time
# A deadline on each wait: an emulator that never starts fails the step instead of the job's timeout.
timeout 300 "$ADB" wait-for-device || { echo "emulator $AVD did not start"; tail -20 "dist/ui-smoke-emulator-$AVD.log"; exit 1; }
echo "emulator $AVD: Android $("$ADB" shell getprop ro.build.version.release | tr -d '\r') (API $("$ADB" shell getprop ro.build.version.sdk | tr -d '\r')), ABIs $("$ADB" shell getprop ro.product.cpu.abilist | tr -d '\r')"
deadline=$((SECONDS + 600))
until [ "$("$ADB" shell getprop sys.boot_completed | tr -d '\r')" = "1" ]; do
  [ $SECONDS -lt $deadline ] || { echo "emulator $AVD did not finish booting"; exit 1; }
  sleep 5
done
"$ADB" install -r "$APK"
"$ADB" logcat -c
"$ADB" shell am start -n "$PKG/org.beeware.android.MainActivity"
alive() { "$ADB" shell pidof "$PKG" >/dev/null; }
fail() { echo "$1"; "$ADB" logcat -d > $OUT/logcat.txt; grep -E "AndroidRuntime|python\.std" $OUT/logcat.txt | tail -60; exit 1; }
sleep 45
alive || fail "the app is not running after start"
"$ADB" exec-out screencap -p > $OUT/1-start.png
# Find "Try a sample" from the UI tree; uiautomator is flaky on emulators, so fall back to where the
# button sits on a 1080x1920 screen (the first of three equal buttons' middle).
POS=""
for _ in 1 2 3; do
  "$ADB" shell uiautomator dump /data/local/tmp/ui.xml || true
  if "$ADB" pull /data/local/tmp/ui.xml $OUT/ui.xml >/dev/null 2>&1; then
    POS=$(python3 - $OUT/ui.xml <<'PY'
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
  POS="$((W * 3 / 4)) $((H * 579 / 1920))"  # row 3, right: "Try a sample"
  echo "uiautomator gave no tree; tapping the button's usual place: $POS"
fi
"$ADB" shell input tap $POS
for _ in $(seq 1 30); do
  sleep 5
  alive || fail "the app stopped while reading the sample"
  if "$ADB" logcat -d | grep -q "HeOCR read sample.png"; then break; fi
done
"$ADB" exec-out screencap -p > $OUT/2-sample.png
"$ADB" logcat -d > $OUT/logcat.txt
LINE=$(grep -o "HeOCR read sample.png: .*" $OUT/logcat.txt | tail -1 || true)
[ -n "$LINE" ] || fail "the sample was not read within 150 seconds"
echo "$LINE"
case "$LINE" in *": ok "*) ;; *) fail "the sample did not read as ok";; esac
alive || fail "the app stopped after reading the sample"

# Shares from "another app" while HeOCR is open: put a file where the app's own FileProvider serves
# it (cache/shared/), then send it with ACTION_SEND to the running activity. File managers often send
# */* rather than the real type, so the bill goes both ways.
AUTH=$("$ADB" shell dumpsys package "$PKG" | grep -o '[A-Za-z0-9_.-]*\.fileprovider' | head -1)
[ -n "$AUTH" ] || fail "no FileProvider authority for $PKG"
echo "FileProvider: $AUTH"
share() {  # share <local file> <name on the device> <mime> <expected route text>
  "$ADB" push "$1" "/data/local/tmp/$2" >/dev/null
  "$ADB" shell chmod 644 "/data/local/tmp/$2"
  "$ADB" shell run-as "$PKG" mkdir -p cache/shared
  "$ADB" shell run-as "$PKG" cp "/data/local/tmp/$2" "cache/shared/$2"
  "$ADB" logcat -c
  # adb shell hands the line to the device's shell: quote the type, or */* is expanded as a glob there.
  "$ADB" shell am start -a android.intent.action.SEND -t "'$3'" \
    --eu android.intent.extra.STREAM "content://$AUTH/shared/$2" \
    --grant-read-uri-permission -n "$PKG/org.beeware.android.MainActivity" >/dev/null
  for _ in $(seq 1 24); do
    sleep 5
    alive || fail "the app stopped after sharing $2 as $3"
    if "$ADB" logcat -d | grep -q "HeOCR read $2"; then break; fi
  done
  "$ADB" logcat -d >> $OUT/logcat.txt
  LINE=$("$ADB" logcat -d | grep -o "HeOCR read $2: .*" | tail -1 || true)
  COPY=$("$ADB" logcat -d | grep -o "HeOCR incoming $2: .*" | tail -1 || true)
  echo "$COPY"; echo "$LINE"
  [ -n "$LINE" ] || fail "$2 shared as $3 was not read within 120 seconds"
  case "$LINE" in *": ok "*"$4"*) ;; *) fail "$2 shared as $3 did not read as ok with $4";; esac
}
FIXTURES="${FIXTURES:-tests/fixtures}"
share "$FIXTURES/garden.pdf" garden.pdf application/pdf "'text_layer': 1"
"$ADB" exec-out screencap -p > $OUT/3-shared.png
if [ -f "$FIXTURES/itext-style.pdf" ]; then
  share "$FIXTURES/itext-style.pdf" itext-style.pdf "*/*" "'text_layer': 2"
  share "$FIXTURES/itext-style.pdf" itext-style-2.pdf application/pdf "'text_layer': 2"
  "$ADB" exec-out screencap -p > $OUT/4-shared-bill.png
fi

# "Open a file": the real system picker. Put the bill in Downloads, open the picker from the app, and
# choose it by name from the picker's own screen.
if [ -f "$FIXTURES/itext-style.pdf" ]; then
  PICK=heocr-picker-test.pdf
  "$ADB" push "$FIXTURES/itext-style.pdf" "/sdcard/Download/$PICK" >/dev/null
  "$ADB" shell content call --uri content://media --method scan_volume --arg external_primary >/dev/null 2>&1 || true
  "$ADB" logcat -c
  tap_text() {  # tap_text <regex for text or content-desc>; 0 when tapped
    "$ADB" shell uiautomator dump /data/local/tmp/ui.xml >/dev/null 2>&1 || true
    "$ADB" pull /data/local/tmp/ui.xml $OUT/picker.xml >/dev/null 2>&1 || return 1
    local pos
    pos=$(python3 - $OUT/picker.xml "$1" <<'PY'
import re, sys
xml, want = open(sys.argv[1], encoding="utf-8").read(), sys.argv[2]
for node in re.finditer(r"<node [^>]*>", xml):
    n = node.group(0)
    label = " ".join(x for x in re.findall(r'(?:text|content-desc)="([^"]*)"', n) if x).strip()
    m = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n)
    if m and re.search(want, label, re.I):
        print(f"{(int(m[1]) + int(m[3])) // 2} {(int(m[2]) + int(m[4])) // 2}")
        break
PY
)
    [ -n "$pos" ] && "$ADB" shell input tap $pos
  }
  tap_text "^open a file$" || fail "no 'Open a file' button"
  sleep 6
  "$ADB" exec-out screencap -p > $OUT/5-picker.png
  # The file's own row (exact name), not its "Preview the file …" icon.
  if ! tap_text "^${PICK//./\\.}$"; then
    # Not among the recent files: open the picker's list of places, then Downloads.
    tap_text "show roots|navigation" || true
    sleep 2
    tap_text "^downloads?$" || true
    sleep 3
    tap_text "^${PICK//./\\.}$" || fail "the picker did not show $PICK"
  fi
  for _ in $(seq 1 24); do
    sleep 5
    alive || fail "the app stopped after picking a file"
    if "$ADB" logcat -d | grep -q "HeOCR read $PICK"; then break; fi
  done
  "$ADB" logcat -d >> $OUT/logcat.txt
  LINE=$("$ADB" logcat -d | grep -o "HeOCR read $PICK: .*" | tail -1 || true)
  echo "$LINE"
  [ -n "$LINE" ] || { "$ADB" logcat -d | grep -E "HeOCR|python.std" | tail -20; fail "the picked file was not read"; }
  case "$LINE" in *": ok "*"'text_layer': 2"*) ;; *) fail "the picked file did not read as ok from its text layer";; esac
  "$ADB" exec-out screencap -p > $OUT/6-picked.png
fi
echo "UI smoke passed: started, read the sample, read shared PDFs (*/* and application/pdf), opened one with the picker, still running"
