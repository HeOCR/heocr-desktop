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
# One emulator at a time: the previous step's emulator may still be shutting down, and adb would then
# see two devices. Stop it and wait until adb lists none.
for _ in $(seq 1 30); do
  "$ADB" devices | grep -q "^emulator-" || break
  "$ADB" emu kill >/dev/null 2>&1 || true
  sleep 2
done
"$ADB" devices | grep -q "^emulator-" && { echo "an earlier emulator is still running"; "$ADB" devices; exit 1; }
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
tap_text() {  # tap_text <regex for text or content-desc>; 0 when tapped
  "$ADB" shell uiautomator dump /data/local/tmp/ui.xml >/dev/null 2>&1 || true
  "$ADB" pull /data/local/tmp/ui.xml $OUT/ui.xml >/dev/null 2>&1 || return 1
  local pos
  pos=$(python3 - $OUT/ui.xml "$1" <<'PY'
import re, sys
xml, want = open(sys.argv[1], encoding="utf-8").read(), sys.argv[2]
for node in re.finditer(r"<node [^>]*>", xml):
  n = node.group(0)
  label = " ".join(x for x in re.findall(r'(?:text|content-desc)="([^"]*)"', n) if x).strip()
  m = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n)
  # A node off screen (a link below the fold) has empty bounds: not tappable until scrolled to.
  if m and re.search(want, label, re.I) and int(m[3]) > int(m[1]) and int(m[4]) > int(m[2]):
      print(f"{(int(m[1]) + int(m[3])) // 2} {(int(m[2]) + int(m[4])) // 2}")
      break
PY
)
  [ -n "$pos" ] && "$ADB" shell input tap $pos
}
# The page is a WebView: uiautomator sees its links with their labels. It is flaky on emulators, so retry.
# Between tries, scroll the page up a little: the control may be below the fold.
tap_retry() {
  for i in 1 2 3 4 5; do
    tap_text "$1" && return 0
    [ $i -ge 2 ] && "$ADB" shell input swipe 540 1500 540 900 300
    sleep 2
  done
  return 1
}
seen() { "$ADB" shell uiautomator dump /data/local/tmp/ui.xml >/dev/null 2>&1 || true; "$ADB" pull /data/local/tmp/ui.xml $OUT/ui.xml >/dev/null 2>&1 || return 1; grep -qiE "$1" $OUT/ui.xml; }
logged() { for _ in $(seq 1 10); do "$ADB" logcat -d | grep -q "$1" && return 0; sleep 1; done; return 1; }
# Home at phone scale (design SPEC 6): both buttons on screen and inside its width, before any scroll.
# A page loaded before the WebView had its size draws zoomed, and they fall off the right edge.
home_fits() {
  "$ADB" shell uiautomator dump /data/local/tmp/ui.xml >/dev/null 2>&1 || true
  "$ADB" pull /data/local/tmp/ui.xml $OUT/ui-home.xml >/dev/null 2>&1 || return 1
  python3 - $OUT/ui-home.xml "$("$ADB" shell wm size | grep -o '[0-9]*x[0-9]*' | tail -1)" <<'PY'
import re, sys
xml, width = open(sys.argv[1], encoding="utf-8").read(), int(sys.argv[2].split("x")[0])
found = {}
for n in re.findall(r"<node [^>]*>", xml):
    label = " ".join(x for x in re.findall(r'(?:text|content-desc)="([^"]*)"', n) if x).strip().lower()
    m = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n)
    if m and label in ("open a file", "try a sample"):
        found[label] = tuple(map(int, m.groups()))
ok = len(found) == 2 and all(b[2] > b[0] and b[3] > b[1] and b[2] <= width for b in found.values())
print("home buttons:", found, "screen width", width, "fit" if ok else "DO NOT FIT")
sys.exit(0 if ok else 1)
PY
}
home_fits || { sleep 5; home_fits; } || fail "Home is not at phone scale: its buttons are off screen (zoomed page)"
tap_retry "^try a sample$" || fail "no 'Try a sample' button on the home screen"
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
  "$ADB" shell input keyevent 4  # from the last reading back to Home, where "Open a file" is
  sleep 2
  tap_retry "^open a file$" || fail "no 'Open a file' button"
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
# The design's screens (design/android/SPEC.md): every control is a link the app intercepts.
# Copy: the toast is put into the page from outside (evaluate_javascript under the page's policy).
tap_retry "^copy$" || fail "no Copy button on the result"
logged "HeOCR copied" || fail "Copy did nothing"
sleep 1
seen "text copied" || fail "the copied toast did not show (evaluate_javascript)"
"$ADB" exec-out screencap -p > $OUT/7-copied.png
# More: the sheet opens in place; Back closes it, and Back again goes Home.
sleep 4
tap_retry "^more actions$" || fail "no More button"
logged "HeOCR action more" || fail "More did nothing"
sleep 1
seen "copy technical details" || fail "the sheet did not open"
"$ADB" exec-out screencap -p > $OUT/8-sheet.png
"$ADB" logcat -c
"$ADB" shell input keyevent 4
sleep 2
alive || fail "Back closed the app with the sheet open"
"$ADB" logcat -d | grep -q "HeOCR screen home" && fail "Back left the result instead of closing the sheet"
"$ADB" shell input keyevent 4
logged "HeOCR screen home" || fail "Back on the result did not go Home"
# About, and Copy technical details from it.
tap_retry "^about$" || fail "no About button"
logged "HeOCR screen about" || fail "About did not open"
"$ADB" exec-out screencap -p > $OUT/9-about.png
tap_retry "^copy technical details" || fail "no Copy technical details row"
logged "HeOCR diagnostics copied" || fail "Copy technical details did nothing"
"$ADB" logcat -c
"$ADB" shell input keyevent 4
logged "HeOCR screen home" || fail "Back on About did not go Home"
alive || fail "the app stopped on Back"
# Night and 200% text: the page follows the phone (SPEC 3.6, 3.7).
"$ADB" shell cmd uimode night yes >/dev/null
"$ADB" shell settings put system font_scale 2.0
"$ADB" shell am force-stop "$PKG"
"$ADB" logcat -c
"$ADB" shell am start -n "$PKG/org.beeware.android.MainActivity" >/dev/null
logged "HeOCR screen: night=True text_zoom=200" || { sleep 20; logged "HeOCR screen: night=True text_zoom=200" || fail "the app did not follow night mode and the font scale"; }
sleep 5
"$ADB" exec-out screencap -p > $OUT/10-home-night-200.png
# The reading itself at 200% text, for the screenshot (pinch zoom needs two fingers; not injected here).
# Reported, not failed: on Android 15 the text at 200% is still too large (issue #23), so the button
# can fall off the screen. The screenshots show it.
if tap_retry "^try a sample$"; then
  for _ in $(seq 1 30); do sleep 5; "$ADB" logcat -d | grep -q "HeOCR screen result" && break; done
  "$ADB" logcat -d | grep -q "HeOCR screen result" || echo "WARNING: the sample was not read at 200% text"
  sleep 2
  "$ADB" exec-out screencap -p > $OUT/11-result-night-200.png
else
  echo "WARNING: no 'Try a sample' on screen at 200% text (issue #23)"
fi
"$ADB" logcat -d | grep -o "HeOCR text zoom: .*" | tail -1 || true
"$ADB" shell cmd uimode night no >/dev/null
"$ADB" shell settings put system font_scale 1.0
echo "UI smoke passed: started, read the sample, read shared PDFs (*/* and application/pdf), opened one with the picker, copied, the sheet and Back, About, diagnostics, night and 200% text"
