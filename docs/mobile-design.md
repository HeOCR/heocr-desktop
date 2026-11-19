# HeOCR on phones: design note

Status: proposal, 2026-11-19. Nothing here creates an account, signs anything or publishes anything; those steps are marked **Shay** and wait for his go.

**Recommendation in one line:** Android first, as a second Briefcase app in this repository that runs heocr itself on the phone. MVP: share or open a PDF, DOCX or image, or take a photo, and get the Hebrew text out, fully offline. iOS follows once heocr can run Tesseract in-process, without a subprocess, and pypdfium2 has iOS wheels.

## 1. Goals and constraints, as for the desktop app

- **The same reading as everywhere else.** The phone runs heocr itself, the same version and the same Tesseract models as the desktop app and the release gate, not a re-implementation. A page read on the phone and on the Mac gives the same record.
- **Fully offline, no telemetry.** No network code, no analytics, no crash reporting, no update checks. Files never leave the phone except where the user shares them.
- **Open source, permissive only,** as on the desktop (`THIRD_PARTY_LICENSES.md`).
- **Phone photos are first-class input.** Blur, tilt and compression are real-world conditions. Evaluation measures them on phone captures; the app adds no clean-up of its own beyond rotation, which is the user's choice.

## 2. Architecture: Python on the phone, through Briefcase

| Option | Reading identical to heocr | Work | Verdict |
|---|---|---|---|
| **A. heocr on-device with Briefcase** (Android: Chaquopy/Gradle; iOS: Python-Apple-support). Toga for the native shell. | yes, it *is* heocr | moderate: the native shell is new, `engine.py`, `render.py` and `i18n.py` are reused | **recommended** |
| B. Native apps (Kotlin, Swift) calling Tesseract and PDFium directly | no: heocr's routing, text-layer checks and structure would be re-implemented and drift | large, twice | rejected |
| C. A web app (PWA) with Tesseract in WebAssembly | no, and no PDF text-layer pipeline | large | rejected |

- **One repository, two apps.** A Briefcase project can hold several apps. `pyproject.toml` gains `[tool.briefcase.app.heocr_mobile]`, sharing the engine, the HTML renderer, the strings and the fixtures with `heocr_desktop`.
  - The desktop UI (pywebview) does not run on phones. The mobile shell is Toga: native buttons and a Toga `WebView` that shows `render.py`'s HTML, which is read-only and needs no JavaScript bridge.
  - If both apps ship, renaming the repository to `heocr-apps` is Shay's call; GitHub keeps redirects.

## 3. On-device OCR

**Tesseract** is the same 5.5.3 with the same pinned models, built by `scripts/build_tesseract.py` with vcpkg's Android (`arm64-android`) and iOS (`arm64-ios`) triplets, in CI.

How heocr reaches it:
- **Today heocr runs the `tesseract` program as a subprocess** (`heocr.ocr.tesseract`).
- **Android** allows that when the program is packaged as a native library: `libtesseract_exec.so` in `jniLibs/arm64-v8a/`, run from `applicationInfo.nativeLibraryDir`.
  - Since Android 10 (API 29) an app may not execute files from its writable data folder. The native-library folder is the exception, so the bundled binary has to live there.
  - **The Android MVP can use heocr unchanged.**
- **iOS forbids subprocesses** altogether (`fork`/`exec`). heocr needs an **in-process Tesseract backend**: the Tesseract C API through `ctypes`, with the TSV from `TessBaseAPIGetTsvText`, which is the same renderer the CLI's `tsv` output uses.
  - This is heocr's change to make (pipeline), and must give a byte-identical record to the CLI path, proven on the gate's fixtures.
  - It would also serve Android later, and drop the executable-library trick.
- **Determinism:** our Tesseract build has no OpenMP; the in-process backend runs one page at a time, like the CLI.

**Models:**
- The app ships `heb` (tessdata_best 4.1.0, 3.5 MB) and `eng` (tessdata_fast 4.1.0, 3.9 MB), exactly the desktop pins.
- heocr 0.2.0's bundled HeOCR models (D6, about 3.6 MB each) arrive inside the heocr wheel, exactly as the desktop app will carry them. The app sets `HEOCR_MODELS` to an empty in-app folder, so only bundled files are used.
- Nothing is ever downloaded.

**Size estimate** (to be measured in the first CI build): Android APK, `arm64-v8a` only:

| Component | Size |
|---|---|
| Python runtime and stdlib | 15–20 MB |
| heocr, Pillow, pypdfium2, defusedxml | about 10 MB |
| Tesseract and Leptonica, static | 6–8 MB |
| Models | 7.4 MB (+3.6 MB per HeOCR model) |
| Toga Android | about 5 MB |
| **Total** | **about 45–60 MB** |

Play delivers per-device APKs from an app bundle, so users download one ABI. `armeabi-v7a` (32-bit) can come later; pypdfium2 has wheels for it.

## 4. Dependencies on phones (checked 2026-11-19)

| Package (desktop pin) | Android | iOS |
|---|---|---|
| pypdfium2 5.15.2 | ✅ official wheels on PyPI for `android_23_arm64_v8a` and `armeabi_v7a` | ⚠️ upstream "setup only, untested": no wheels yet |
| Pillow 13.0.0 | ⚠️ no Android wheels on PyPI. Build our own with cibuildwheel ≥ 3.1, which supports Android, or use Chaquopy's package repository if it has 13.0.0. The gate pin matters, so the version must match | ✅ official iOS wheels on PyPI |
| defusedxml 0.7.1, heocr | ✅ pure Python | ✅ pure Python |
| Tesseract and Leptonica | our CI build (vcpkg `arm64-android`) | our CI build (vcpkg `arm64-ios`), linked in-process |

## 5. Input and output

**MVP, Android:**
- **Share sheet:** HeOCR appears when sharing a PDF, DOCX or image from Files, Gmail, WhatsApp, Telegram or the gallery (`ACTION_SEND`, `ACTION_VIEW` intent filters for `application/pdf`, the DOCX MIME type and `image/*`). This is the main way in.
- **Open file:** the system picker (Storage Access Framework, `ACTION_OPEN_DOCUMENT`), called through Chaquopy's Java bridge; Toga's file dialogs are not supported on Android or iOS yet.
- **Camera:** `toga.hardware.Camera.take_photo()` (Android and iOS). The photo is read by OCR as taken; the user can rotate it in 90° steps.
- **Output:**
  - the text, right to left, with its structure (the desktop's formatted, plain and Markdown views);
  - **Copy**;
  - **Share** as text (`ACTION_SEND`);
  - **Save** as .txt, .md or .json (`ACTION_CREATE_DOCUMENT`);
  - the route each page took, and progress page by page with Cancel, as on the desktop.
- **Languages:** Hebrew and English UI, following the system, with `i18n.py` shared.

**Later:** several photos into one document; a crop frame; XLSX, PPTX and HTML (they come free with heocr and only need the MIME filters); an iOS "Open in HeOCR" document type. Briefcase does not build iOS share extensions, so iOS gets the system's Open-in route.

## 6. Offline and privacy

- **Android: no `INTERNET` permission in the manifest.** The operating system then refuses every socket the app opens. It is the strongest guarantee there is, and Play and F-Droid show it on the listing.
- The app also keeps the desktop's in-process network guard (`engine.install_offline_guard`) as a second layer.
- **iOS has no network permission to drop.** The guarantee rests on the in-process guard, no networking code, and the App Store privacy label "Data Not Collected".
- **Permissions:** camera only, asked the first time the user takes a photo. No storage permission, because the system pickers and share sheet grant access per file.
- **Stores:** Play and the App Store keep their own install statistics. The app sends nothing.

## 7. Signing, store accounts and costs

| | Android: F-Droid | Android: Google Play | iOS: App Store |
|---|---|---|---|
| Account | none; a metadata merge request to `fdroiddata` | Play Console developer account (personal) | Shay's existing Apple Developer Program membership covers it |
| Cost | free | US$25 once | nothing extra (US$99/year, already paid) |
| Before the first public release | F-Droid builds from our tagged source; reproducible builds let it ship our signature | a personal account created after 13 Nov 2023 must run a **closed test with at least 12 testers for 14 days** before production. An organisation account skips that, but needs a D-U-N-S number | App Review; TestFlight for testers |
| Signing key | F-Droid's key, or ours with reproducible builds | Play App Signing: Google holds the app key, we hold an **upload key** | Apple Distribution certificate, in Shay's keychain like the Developer ID |
| Listing forms | metadata in the repository | Data safety: "no data collected or shared"; content rating; a public contact email | privacy label "Data Not Collected"; export compliance: no encryption |

**Shay does himself**, because these involve identity, payment, agreements or keys:
- create and verify the Play Console account (government ID; US$25);
- accept the store agreements;
- generate the Android upload keystore and keep it, and if CI signs, add it as a repository secret;
- create the App Store Connect app record and the Apple Distribution certificate;
- recruit the 12 Play testers. The HeOCR volunteers are the natural group.

**Agents do:** the code, CI builds, the store-listing text for Shay to review, the F-Droid metadata (a public merge request, so only on his go), and test builds as CI artifacts that he can sideload.

**Recommended route:**
1. **F-Droid first.** Free, fits an open, offline app, and needs no account from Shay.
2. **Play** when Shay wants the reach. Start the 14-day closed test early, since it is the long pole.
3. **The App Store** with the iOS version.

## 8. Plan

| Step | What | Where | Needs Shay |
|---|---|---|---|
| M0 | Android build in CI: Tesseract for `arm64-android`, Pillow 13.0.0 for Android, Briefcase Android app, smoke test on the fixtures in the Android emulator (GitHub Actions, Linux with KVM). Measure the APK size | CI only | no |
| M1 | MVP features (section 5); debug-signed APK as a CI artifact for Shay's phone | CI only | to sideload and try it |
| M2 | Release: F-Droid metadata MR; Play account and closed test in parallel if wanted | public | yes: the go, the accounts |
| M3 | iOS: heocr's in-process Tesseract backend (pipeline), pypdfium2 iOS wheels (upstream or our build), Toga iOS app, TestFlight | CI on macOS runners | yes: the App Store record |

Local Mac work stays light. Mobile builds and emulator tests run on GitHub Actions, never during an evaluation run on the Mac.

## 9. Decisions for Shay and the lead

1. Android first, with F-Droid as the first store: yes or no?
2. One repository with two Briefcase apps (later renamed `heocr-apps`), or a separate `heocr-mobile`?
3. Ask pipeline for the in-process Tesseract backend in heocr now. It is needed for iOS, and is optional for Android.
4. Play: a personal account with the 12-tester closed test, or an organisation account (needs a legal entity and D-U-N-S)?

## Sources

- Google Play: [testing requirements for new personal developer accounts](https://support.google.com/googleplay/android-developer/answer/14151465)
- pypdfium2: [platform support](https://pypdfium2.readthedocs.io/en/stable/platforms.html); PyPI file list of pypdfium2 5.15.2 and Pillow 13.0.0, checked 2026-11-19
- Toga: [Camera](https://toga.beeware.org/en/stable/reference/api/hardware/camera/), [dialogs](https://toga.beeware.org/en/latest/reference/api/application/dialogs/) ("not currently supported on Android or iOS" for file dialogs)
- Android 10 and executing bundled binaries: [Android issue tracker 152645643](https://issuetracker.google.com/issues/152645643)
- PyPI accepting iOS and Android wheels, and cibuildwheel 3.0 (iOS) and 3.1 (Android): [BeeWare status updates, 2025](https://beeware.org/news/buzz/2025/july-2025-status-update/)
