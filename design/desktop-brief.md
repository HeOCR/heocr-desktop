# Design brief: the HeOCR desktop apps (macOS and Windows)

You are HeOCR's designer. Design the desktop app for macOS and Windows in the **Bounding Box** brand, as you did for the Android app. Bring it to the same level of care, and make it a real desktop app rather than a stretched phone screen.

Sign your work `design[claude/claude-code#shay-macbook-m4]@heocr/opensource`. Send the PR to the lead session, "heocr-lead" (`local_2d4f4d62-d2ea-4a71-80bf-ffa0e42b5aaf`), and never merge your own PR. The app's maintainer is the session "heocr-app" (`local_efba2c9b-af32-4e42-97a7-6a0512326474`). Ask it about anything technical through the lead.

---

## 1. What the app is

The repository is `HeOCR/heocr-desktop`. Read `README.md` and `AGENTS.md` first.

- **What it does:** you drop in a PDF, a Word file, an image, an Excel or PowerPoint file, or a saved web page, and get its Hebrew text out, with headings, paragraphs, lists and tables. It runs fully offline.
- **How it's built:** Python in [Briefcase](https://briefcase.readthedocs.io), with the window drawn by [pywebview](https://pywebview.flowrl.com). On macOS the window is WebKit (macOS 13 and later); on Windows it is WebView2 (Windows 10 and 11).
- **The interface is one HTML page:** `src/heocr_desktop/ui/index.html`, `app.css` and `app.js`. Python fills it through `set_content` and talks to it through a small JS API (see `src/heocr_desktop/app.py`).
- **Strings** are in `src/heocr_desktop/i18n.py`, in Hebrew and English.
- **What exists today:**
  - three result views: formatted, plain text and Markdown;
  - a statement of how the text was read: the PDF's text layer, OCR, or the file itself;
  - page-by-page progress with Cancel;
  - copy, and save as `.txt`, `.md` or `.json`;
  - a Hebrew/English toggle, and an About box with the licences.
- **Coming:** saving as `.docx` (heocr 0.3.0). Leave a place for it.
- **Status:** 0.1.0 is released, unsigned on Windows for now. Look at it before you start: build it or run it from source as `README.md` describes, and take screenshots of today's app in both languages.

## 2. Hard technical limits

- **No network, ever.** The page runs under a content security policy of `default-src 'none'`, and the app refuses every connection. So:
  - no web fonts, no remote images, no CDN;
  - fonts come in as data URIs, as in `design/android/css/fonts-embedded.css`;
  - images come in as inline SVG or data URIs.
- **One page:**
  - screens are states of one document, switched by classes, not separate pages;
  - no framework; plain HTML, CSS and a little JS, which heocr-app will wire up.
- **Native where the system owns it:** the open and save dialogs, the menu bar, the window frame and title bar, and the Dock and taskbar stay native. You design what is inside the window, plus the menu labels.
- **Both engines:** what you use must work in WebKit (Safari 16) and in WebView2 (current Chromium). Check `:has()`, `color-mix()`, container queries and so on against Safari 16.

## 3. Build on what exists, don't fork it

- **The brand:** `HeOCR/heocr.github.io`, `design/brand-handover/`. Read `BRAND.md`, and use `tokens/` and `logo/`. One brand blue on white, square corners, hairlines, no shadows, no gradients. JetBrains Mono for Latin headings and labels, Noto Sans Hebrew for Hebrew. The box only on the logo, a title or one hero element.
- **The Android design** in this repository, `design/android/`. Start from its `SPEC.md`, `css/tokens.css`, `css/result.css`, `fonts/` and `icons/in-app/`.
  - The result view should be the same stylesheet on both platforms, or one with a small desktop layer on top.
  - Reuse the tokens and icons. Where desktop needs something new (a drop zone, a split view, keyboard focus), add it as an extension and list it, as the Android spec's section 16 did.
- **The review app** (`HeOCR/heocr-review`, `design/review/`) and the **asset pack** (`HeOCR/heocr.github.io`, `design/asset-pack/`) are the other recent work to stay consistent with.

## 4. What to design

### 4.1 The window
- **Sizes:** a minimum of about 720 × 520, a typical 1100 × 760, and a large 1600 × 1000. The layout must work at all three, and when resized.
- **Mac and Windows:** respect each system's conventions where users expect them, for example the space for the traffic lights if you use the title-bar area, and Windows' focus and scrollbar behaviour. Inside the window the look is HeOCR's on both.
- **Theme:** light and night follow the system (`prefers-color-scheme`).
- **Direction:** Hebrew right to left, English left to right, following the toggle. Mixed text in the result follows each block's own direction, as `result.css` already does.

### 4.2 Screens and states
1. **Start / empty:** the drop target and **Open file…**, with a short line on what the app opens and the offline promise, in the README's approved wording. The drop state while a file is dragged over the window counts too: the whole window is the target.
2. **Reading:** the file's name and type, page-by-page progress for long PDFs, and Cancel. Use the brand's scan-box motion from the Android spec, calmer at desktop size.
3. **Result:**
   - the text with the three views (formatted, plain, Markdown);
   - how it was read (text layer / OCR / file), and that OCR text may have mistakes;
   - the parts that could not be read;
   - Copy and Save (`.txt`, `.md`, `.json`, and later `.docx`);
   - "Open another file".
   - Long documents (hundreds of pages) must stay readable and fast to scroll. Consider a slim page or section index on wide windows.
4. **Problem states:**
   - unsupported formats: `.doc`, RTF and OpenDocument need LibreOffice, which the app doesn't include, so ask the user to save as DOCX or PDF;
   - a damaged file;
   - a file with no text found;
   - a cancelled read.
5. **About:** the version, the licence, the bundled components and their licences (from `THIRD_PARTY_LICENSES.md`), and links to heocr.org and GitHub, which open in the system browser.
6. **Settings, if any:** today only the language. Don't add settings the app doesn't have.

### 4.3 Desktop interaction
- **Keyboard:** the whole app works from the keyboard, with visible focus. Propose shortcuts: Open (⌘O / Ctrl+O), Copy all, Save (⌘S / Ctrl+S), switching views, Cancel (Esc). Show them in the menus and in tooltips.
- **Menus:** give the menu labels for both systems, in Hebrew and English (File, Edit, View, Help), using only actions that exist.
- **Text selection:** in the result, selecting and copying part of the text must work and keep the direction right.
- **Text size:** follow the system's text size, and allow zoom in the result.

### 4.4 Icons and installers
- **App icon:**
  - macOS `.icns`, from a 1024 master on the current macOS icon grid;
  - Windows `.ico` (16, 24, 32, 48, 64, 128, 256), legible at 16 px;
  - start from the Android launcher icon (white ground, the mark), so the apps look like one family.
- **Installers:**
  - a DMG window background, with the app and the Applications shortcut;
  - for the Windows MSI, the installer's banner and dialog images, if Briefcase's MSI template supports them. Check its documentation and say what it supports, with the date you checked.
- **In-app icons:** reuse `design/android/icons/in-app/`, and add only what desktop needs. Note which ones mirror in Hebrew.

## 5. Deliverables

One PR to `HeOCR/heocr-desktop` under `design/desktop/`, with a `README.md` index and a `SPEC.md` written the way `design/android/SPEC.md` is.

- **SPEC.md:**
  - the decisions;
  - the tokens and their extensions;
  - every component with its sizes and states;
  - the screen flow;
  - keyboard and menus;
  - motion, right to left, and accessibility;
  - what heocr-app must provide;
  - open questions.
- **css/:** drop-in stylesheets for the page, with the fonts embedded, plus a one-file standalone build.
- **mockups/:** every screen and state as static HTML on those stylesheets, in `he/` and `en/`, plus PNG renders at 1100 × 760 and 720 × 520, light and night.
- **icons/:** the app icon sources and exports, the DMG background, and the MSI images (if supported).
- **strings/strings.json:** every string in Hebrew and English. Mark which reuse approved wording (the Android `strings.json` and the README) and which are new; new Hebrew needs the owner's review.

Don't change app code. heocr-app implements from your files.

## 6. Rules
- **Truthfulness:**
  - no figures, no accuracy claims, and no comparisons anywhere in the interface;
  - the privacy wording follows the README's ("Fully offline", "Your files never leave your computer");
  - no partner names, no people's names or photos.
- **Content:** sample text in mockups is invented Hebrew and English. Never use the project's real scans or documents, because some are evaluation data or private.
- **Accessibility:** AA contrast with the brand tokens, every control reachable by keyboard and labelled for screen readers (VoiceOver and Narrator), and nothing that moves when the system asks for reduced motion.
- **Fonts and licences:** Noto Sans Hebrew and JetBrains Mono (OFL), subset as in `design/android/fonts/subset_fonts.py`. List every source in the README.

## 7. Show direction first

Start with one small PR containing:
- the start screen with the drop state, and the result screen, at 1100 × 760, in Hebrew light and English night;
- two app icon options next to the Android launcher icon, at 16, 32 and 128 px;
- your SPEC's "decisions in short" section.

Taste questions go through the lead to the owner. The full set comes after that answer.
