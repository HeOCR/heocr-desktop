# HeOCR desktop: design specification

The Bounding Box brand on macOS and Windows. Written the way `design/android/SPEC.md` is, and built on it: the same tokens, the same result stylesheet, the same icons. Sizes are CSS px. Designed at 1100 × 760, checked at 720 × 520 and 1600 × 1000, in light and night, in Hebrew (right to left) and English.

Owner decisions this follows: app icon option B (the mark fills the tile); Save is one filled button with a menu of formats; the index of pages and headings stays on wide windows.

## 1. Decisions in short

| Question | Decision |
|---|---|
| Whose window frame? | **The system's.** Title bar, traffic lights, window buttons, menu bar, open and save dialogs stay native. The design starts below the title bar, so nothing is reserved for the traffic lights. |
| The app's own chrome | One 48 px bar: the lockup at the start; the language toggle and About at the end. |
| How screens are switched | One page. A class on `<body>` shows one `<section>`: `is-start`, `is-reading`, `is-result`, `is-message`. Overlays add `is-dragging`, `menu-open`, `about-open`, `toast-on`. The section and control ids are today's where they exist. |
| Where a file lands | The start screen's drop zone is the one boxed element. While a file is over the window, the whole window is the target. |
| The main action on the result | **Save**, the one filled button, with a menu of formats. Copy is beside it, outlined. |
| Long documents | An index of pages and headings on the start side from 900 px wide; the text keeps a reading width. |
| Result stylesheet | `css/result.css` is the Android file, byte for byte. `desktop.css` adds the window around it. |
| Control size | 32 px buttons, 30 px index rows and menu items of 34 px: desktop sizes. |
| Light or dark | The system decides. No toggle. |
| Engines | Safari 16.0 and current Chromium. No `color-mix()`, no CSS nesting, no container queries. |
| Fonts | The Android subsets as data URIs: 51 KB of font data. The page's policy gains `font-src data:`. |
| Script | The design needs none beyond what `app.js` already does: switching classes, filling text. |

## 2. Tokens

`css/tokens.css` is the Android file (only its first comment line differs). Desktop extensions, in `desktop.css`:

| Token | Light | Night | Used for |
|---|---|---|---|
| `--drop-bg` | `#eef1ff` | `#1b2040` | The full-window drop veil; the scan cursor's fill |
| `--focus` | `--accent` | `--accent` | Keyboard focus ring |
| `--bar-h` | 48 | | The app bar |
| `--index-w` | 184 (232 from 1400 wide) | | The index column |
| `--read-w` | 760 (820 from 1400 wide) | | The reading width of the result |
| `--doc-zoom` | 1 | | Text size of the result, set by the zoom control |

**Type.** As on Android: Noto Sans Hebrew for Hebrew and body text, JetBrains Mono for the wordmark, file names, chips, key caps and figures.

| Role | Size / line height |
|---|---|
| Start title | Hebrew 34 / 41 bold (Noto Sans Hebrew); English 30 / 36 bold (JetBrains Mono, tracking −0.03em). 28 and 26 under 900 wide |
| Drop zone title, problem title | 20 / 26 and 21 / 27 bold |
| Body, lede | 15 / 23 and 16 / 25 |
| Buttons | 14, medium; the filled button bold |
| Index rows, segmented control, notices | 13.5 to 14 |
| File name | JetBrains Mono 500, 14 |
| Chips, labels, key caps | JetBrains Mono 500, 11 to 12 |
| Result body | 17 / 29, from `result.css`, times `--doc-zoom` |
| Plain text view | 16 / 28; Markdown view JetBrains Mono 14 / 24.5 (Hebrew falls to Noto Sans Hebrew) |

## 3. The window

- **Sizes.** Minimum 720 × 520; typical 1100 × 760; large 1600 × 1000. Set the window's minimum size to 720 × 520 in pywebview.
- **Under 900 wide:** the index is hidden, "Another file" shows its icon only, the reader's side padding drops to 20.
- **Under 600 high:** the start and reading screens tighten (smaller drop zone, shorter scan box) so nothing scrolls at 720 × 520.
- **From 1400 wide:** the index and the reading width grow one step. The text never spans the window.
- **macOS.** Native title bar with the title "HeOCR"; the menu bar carries the menus of section 9. Nothing is drawn in the title-bar area.
- **Windows.** Native title bar. Scrollbars are the system's; `scrollbar-gutter: stable` keeps the text from shifting when one appears (ignored by Safari 16, harmlessly). Focus rings show for keyboard use only (`:focus-visible`), as Windows users expect.
- **Selection.** The interface is not selectable (`user-select: none`); the result, file names, message text and the licence list are.

## 4. Screens and flow

```
start ──(drop, Open file…, ⌘O)──► reading ──► result ──(Another file, ⌘O, drop)──► reading …
  ▲                                  │            │
  │                                  │            └─ Save ▾, Copy, views, zoom, index
  │                                  ├─ Cancel / Esc ──► message: stopped
  └──────── message ◄────────────────┘  (needs converting · could not be read · no text)
About: from the bar, the Help menu, or the app menu on macOS; over any screen.
```

| # | Screen | Mockup | Notes |
|---|---|---|---|
| 1 | Start | `01-start` | Over the brand grid: the tagline, one sentence, the drop zone (the box with handles) holding the icon, "Drop a file here", "or", **Open file…** and the line of formats; then the offline promise with the lock icon. |
| 1b | File over the window | `02-start-dragging` | A veil covers the whole window in `--drop-bg`; 22 px inside it, a 2 px box with four handles, the drop icon, "Drop to read the file" and "Anywhere in the window". It appears over any screen, not only the start, because a new file can be dropped on a result too. |
| 2 | Reading | `03-reading` | A 520 px column: the file card (type icon, name, type and pages), the scan box, "Page 2 of 3" with elapsed time, one segment per page, a quiet line, Cancel at the end side with its key cap. Files without pages show "Reading…" and one segment. |
| 3 | Result | `04` to `09` | Section 5. |
| 4 | Problems | `10` to `13` | Section 6. |
| 5 | About | `14-about` | Section 7. |
| 6 | Settings | | None. The only setting is the language, and it is the toggle in the bar and an item in the View menu. |

## 5. The result

Three rows above the text, then the split.

1. **Toolbar:** the file name (mono, one line, ellipsis; `<bdi>` so a Hebrew name reads correctly in an English window) with chips for pages and time. At the end: **Copy** (outlined), **Save ▾** (filled), **Another file** (quiet).
2. **View bar:** the segmented control (Formatted, Text, Markdown), the zoom control (smaller, percentage, larger), and at the end "How it was read:" with a chip: text layer, OCR, or document file. A document read in more than one way gets more than one chip.
3. **Split:** the index, then the reader.

**Index** (`nav.index`): a "Pages" label, then one row per page (number, then the page's first heading or "Page n") and indented rows for the other headings on that page. The row for the part in view is marked (`aria-current="true"`: tag ground, 2 px accent bar on its start side). Clicking scrolls the reader. For files without pages (Word, web pages) the index lists headings only; with no headings and one page it is hidden and the reader takes the width. Hundreds of pages: the index scrolls on its own and stays at 30 px per row; it is the fast way through a long document.

**Reader:** scrolls on its own; inside it a column of `--read-w`, centred. First the notices, then the document.

- **Unread parts** (`.notice`): tag ground, warning icon, counted in plain words, pointing at the JSON record for details. Not red.
- **OCR caution:** the app's existing note as the first line of the document, styled quietly by `result.css`, present whenever OCR was used.
- **The document** (`article.doc`): `result.css`, unchanged. Each block keeps its own direction; tables scroll sideways in their own frame; headers, footers and notes are sections at the end.
- **Text view** (`pre.doc.plain`): the same column, wrapped, each line taking its own direction.
- **Markdown view** (`pre.doc.plain.mono`): monospace, every line in the document's direction so table rows stay together.

**Performance for long documents.** Add `content-visibility: auto` with `contain-intrinsic-size` to page-sized chunks of the document if scrolling is slow; Chromium honours it, and Safari 16 ignores it without harm. This is a suggestion for heocr-app to measure, not a requirement.

**Zoom.** The control and the View menu set `--doc-zoom` from 0.8 to 2 in steps of 0.1, applied with the `zoom` property to the reader's column (supported by both engines). It changes the result only, never the window's chrome. The system's own text size is followed by leaving the page's base font size alone.

**Save.** The button opens a menu under it (`.menu`, 268 wide, rows 34 high, icon, label): **Word file (DOCX)** first once it ships, then Text (TXT), Markdown (MD), Full JSON record. Each opens the system's save dialog with the source name and the new extension. `⌘S` / `Ctrl+S` saves in the first format of the menu directly. `07-result-save-menu` is the menu today; `07b` is the menu with Word. The Word item is hidden until heocr 0.3.0, as the current `hidden` attribute does.

**Confirmations** (`.toast`, bottom end corner, 4 s; 8 s with an action): "Saved" with the file name and **Show in folder**; "Copied". `role="status"`.

**Copy.** `⌘C` / `Ctrl+C` copies the selection when there is one. The Copy button and `⇧⌘C` / `Ctrl+Shift+C` copy all the text of the current view. Copied text keeps logical order, so it pastes correctly into right-to-left and left-to-right editors alike.

## 6. Problem states

One layout (`.message`, a 520 px column, centred): a 52 px framed icon, the file name, a title that says what happened, the app's existing sentence, an optional hint, and the actions.

| State | Mockup | Icon | Title | Body | Actions |
|---|---|---|---|---|---|
| Needs converting (`.doc`, RTF, OpenDocument) | `10` | Word document | "This file needs converting first" | The existing `needs_converter` string, unchanged | **Choose another file…** |
| Could not be read | `11` | warning | "This file could not be read" | Existing `unreadable` | **Choose another file…** |
| No text found | `12` | image | "No text found" | Existing `empty`, plus a hint about photos | **Choose another file…** |
| Reading stopped | `13` | close | "Reading stopped" | Where it stopped; nothing was saved | **Read it again**, Choose another file… |

No red, no error codes on screen. The section is `role="alert"` so a screen reader announces it.

## 7. About

A modal `<dialog>` (600 wide, scrolls inside the window when the window is short), opened from the bar, Help, or the app menu on macOS; `Esc` or Close dismisses it and returns focus to where it was.

Top to bottom: the lockup; the version line; the app's existing paragraph; the offline promise; **Links (open in your browser)**: heocr.org and the GitHub repository, each with the external icon; **Licence**: Apache-2.0; **OCR models** with their licences; a disclosure, "Included components and their licences", holding the text of `THIRD_PARTY_LICENSES.md` in a selectable block. Versions and licences in the mockup are examples; the app fills them from its build.

The links must open the system browser. The app never loads them itself.

## 8. Components

States: default / hover / pressed / disabled / focus. Focus is a 2 px `--accent` outline, 2 px away, on `:focus-visible`.

| Component | Class | Size | Default | Hover and pressed | Disabled |
|---|---|---|---|---|---|
| Button | `.btn` | 32 high, 12 side padding, 14 text | 1 px `--control-line`, ground `--bg` | border `--accent`, ground `--accent-soft` | ground `--tag`, border `--line`, text `--muted` |
| Filled button | `.btn.primary` | same; `.large` is 40 | ground and border `--accent`, text `--on-accent`, bold | `--accent-press` | as above |
| Quiet button | `.btn.quiet` | same | no border | ground `--accent-soft` | |
| Icon button | `.iconbtn` | 30 × 30 | icon 20 | ground `--accent-soft` | |
| Segmented control | `.seg` | 30 high | 1 px `--control-line`; selected: ink ground, bold (`aria-selected="true"`) | ground `--accent-soft` | |
| Key cap | `kbd` | 18 high, mono 11 | 1 px `--line-strong`; on the filled button it takes the button's colour | | |
| Chip | `.chip` | mono 11.5 | ground `--tag`, text `--muted` | | |
| Drop zone | `.dropzone` | 640 wide max | 1.5 px `--accent`, four 9 px handles | not a control; the button inside is | |
| Drop veil | `.dropveil` | the window | ground `--drop-bg`, 2 px box 22 px inside | | |
| File card | `.filecard` | | 1 px `--line-strong`, icon 24 muted | | |
| Scan box | `.scan` | 250 high min | 1.5 px `--accent`, handles, nine 8 px lines | | |
| Page segments | `.pages i` | 5 high | done and current `--accent`, to come `--line` | | |
| Index row | `.index button` | 30 high | text 13.5; sub-rows muted and indented | ground `--accent-soft`; current: tag ground, accent bar | |
| Notice | `.notice` | | ground `--tag`, icon 20 muted | | |
| Menu | `.menu` | 268 wide, rows 34 | 1 px `--control-line`, ground `--bg`, no shadow | row ground `--accent-soft` | |
| Toast | `.toast` | 40 high min | the Android toast colours | | |
| Dialog | `dialog#about` | 600 wide | 1 px `--control-line`, over `--scrim` | | |
| Message | `.message` | 520 wide | framed 52 px icon, title 21 bold | | |

The box appears in three places only: the logo, the drop zone (and its full-window form), and the scan box.

## 9. Keyboard and menus

Everything works from the keyboard. Tab order is document order: bar, then the screen's controls from start to end. The reader is focusable so arrow keys, Page Up and Page Down, Home and End scroll it. Menus open with Enter, Space or the down arrow; arrows move; Esc closes and returns focus to the button. Tooltips (`title`) name the action and its shortcut.

| Action | macOS | Windows |
|---|---|---|
| Open… | ⌘O | Ctrl+O |
| Save (first format in the menu) | ⌘S | Ctrl+S |
| Save As… (opens the format menu) | ⇧⌘S | Ctrl+Shift+S |
| Close the file (back to start) | ⌘W | Ctrl+W |
| Copy the selection | ⌘C | Ctrl+C |
| Copy all text | ⇧⌘C | Ctrl+Shift+C |
| Select all (the result) | ⌘A | Ctrl+A |
| Formatted / Text / Markdown | ⌘1 / ⌘2 / ⌘3 | Ctrl+1 / Ctrl+2 / Ctrl+3 |
| Larger / smaller / actual size | ⌘+ / ⌘− / ⌘0 | Ctrl++ / Ctrl+− / Ctrl+0 |
| Cancel the reading; close a menu or About | Esc | Esc |
| Quit | ⌘Q | Alt+F4 |

**Menu labels.** Only actions that exist. Items that do not apply on a screen are disabled, not hidden. `strings/strings.json` has every label under `menus`.

| Menu | English | Hebrew |
|---|---|---|
| App (macOS only) | About HeOCR · Quit HeOCR | אודות HeOCR · יציאה מ-HeOCR |
| File | Open… · Save · Save As… · Close File · Exit (Windows) | קובץ: פתיחה… · שמירה · שמירה בשם… · סגירת הקובץ · יציאה |
| Edit | Copy · Copy All Text · Select All | עריכה: העתקה · העתקת כל הטקסט · בחירת הכול |
| View | Formatted · Text · Markdown · Larger Text · Smaller Text · Actual Size · עברית / English | תצוגה: מעוצב · טקסט · Markdown · הגדלת הטקסט · הקטנת הטקסט · גודל רגיל · English |
| Help | HeOCR Website · HeOCR on GitHub · About HeOCR (Windows) | עזרה: האתר של HeOCR · HeOCR ב-GitHub · אודות HeOCR |

On Windows a menu bar inside a pywebview window may not be available in the same way; if it is not, the same actions stay reachable through the shortcuts and the on-screen controls, and nothing in the design depends on the menu bar.

## 10. Motion

| What | Motion |
|---|---|
| Scan box | The cursor steps one line every 2 s over nine lines (18 s loop); the line it leaves darkens. Slower than the phone's 1.2 s: at desktop size the faster step reads as busy. |
| Current page segment | Opacity 100% → 40% → 100% over 2.4 s |
| Everything else | No motion. States change at once; the veil, menu, toast and dialog appear without transition. |

With reduced motion requested (`prefers-reduced-motion`), the cursor and the segment stand still at the middle.

## 11. Right to left and left to right

- The language toggle sets `<html lang dir>`; the layout uses logical properties and mirrors with `dir` alone.
- Always left to right, isolated: the wordmark, file extensions, versions, times, key caps, licence names, addresses.
- File names use `<bdi>`.
- The result takes the document's direction on `article.doc` and each block keeps its own (`result.css`). The index rows use `dir="auto"`.
- The index is on the start side: the right in Hebrew, the left in English. The toast and the end-side actions follow the same rule.
- Icons that mirror in Hebrew: Back, chevron and external link (as on Android). The new desktop icons do not mirror. `icons/in-app/icons.json` flags each.
- Selection across mixed text follows the browser's logical order; no `user-select` tricks are used inside the result.

## 12. Accessibility

- **Contrast** (AA): the Android table applies unchanged. New pairs: text on `--drop-bg` 16.6 light and 13.3 night; muted text on it 5.6 and 5.9; the accent on it 5.6 and 6.7; toast text on toast 18.7 and 15.5.
- **Keyboard:** section 9. 298 controls in the mockups were checked by script: every one is a native button, link or summary, and every one has a text label or an `aria-label`.
- **Screen readers (VoiceOver, Narrator):** decorative icons are `aria-hidden`; the reading section is `aria-live="polite"` and its progress line `role="status"`; problems are `role="alert"`; the toast is `role="status"`; the view switch is a `tablist` with `aria-selected`; Save has `aria-haspopup="menu"` and `aria-expanded`; the index is a labelled `nav` with `aria-current`; the dialog is labelled by its title.
- **Not colour alone:** the current index row has a bar and bold text; the selected view is inverted and bold; notices have an icon and words.
- **Targets:** pointer targets are at least 30 px high except text links in About (24).
- **Text size:** the page uses the web view's default size, so the system setting scales it; the zoom control scales the result further.
- **Motion:** section 10.

## 13. Icons and installers

**App icon** (`icons/app-icon/`): a white tile with the mark filling it, in the Android launcher's family.

- **macOS:** drawn on the macOS icon grid (an 824 tile with a 185 radius on a 1024 canvas, a hairline edge so it holds on a white Dock or Finder window). `macos/heocr.icns`, `macos/heocr.iconset/` and `macos/heocr-1024.png`.
- **Windows:** the tile fills the canvas so no size is lost to a margin. `windows/heocr.ico` holds 16, 24, 32, 48, 64, 128 and 256.
- **Small sizes** (16, 24, 32) are drawn on the pixel grid by hand, with whole-pixel strokes; they are in both files.
- `repo-icons/` has the same files under the names the repository's `icons/` folder uses today.
- The `.icns` was written without a Mac and lacks the 16 and 32 pt base entries; run `iconutil` on the iconset for the complete file.

**DMG** (`icons/installer/dmg-background.png`, `@2x`): 660 × 400, the grid, the lockup, an arrow from the app's place (180, 200) to Applications (480, 200), and one line in each language. **Briefcase does not use it:** its documentation says "macOS apps do not support splash screens or installer images" (checked 2026-11-20, [briefcase.beeware.org](https://briefcase.beeware.org/en/latest/reference/platforms/macOS/)). It is here for a custom DMG step, if the project adds one.

**Windows MSI** (`icons/installer/msi-dialog-493x312.bmp`, `msi-banner-493x58.bmp`): Briefcase supports both, as `installer_background` ("a 493x312px BMP", the first page) and `installer_banner` ("a 493x58px BMP", the top of every other page), per its Windows page checked 2026-11-20 ([briefcase.beeware.org](https://briefcase.beeware.org/en/latest/reference/platforms/windows/)). That page documents a development version; confirm the options exist in the Briefcase version the repository pins. The dialog image keeps its art in the left 164 px and leaves the rest white for the installer's text; the banner keeps the mark at the right end. The same page lists the icon sizes Briefcase asks for in the `.ico`: 16, 32, 48, 64 and 256, all present.

**In-app icons** (`icons/in-app/`): fourteen from the Android set, unchanged, and six new: `drop`, `language`, `zoom-in`, `zoom-out`, `markdown-file`, `json-file`.

## 14. Brand extensions made for the desktop

1. `--drop-bg` and the full-window drop veil: the box as a target the size of the window.
2. Desktop control sizes (32, 30, 34) and the key cap.
3. The segmented control and the menu, built from hairlines and the 2 px radius, with no shadow.
4. The index column with its current-row bar.
5. The scan box at a slower step.
6. The app icon's filled-tile proportions and the pixel-drawn 16, 24 and 32.
7. Six icons.
8. The zoom control and `--doc-zoom`.

The segmented control and key cap match the review app's; the toast and notice match Android's.

## 15. What heocr-app must provide

1. **Swap the stylesheet.** Replace the `/*STYLE*/` block with `css/desktop-standalone.css`, and add `font-src data:` to the page's policy. Nothing else in the policy changes.
2. **Markup.** Move `index.html` to the structure in `mockups/*/04-result-formatted.html` (every mockup is the whole page). Ids kept from today: `view-result`, `view-message`, `dropzone`, `open`, `lang`, `about-open`, `work-name`, `work-status`, `meter`, `cancel`, `result-name`, `chips`, `copy`, `again`, `notes`, `doc-formatted`, `doc-text`, `doc-markdown`, `message-text`, `message-again`, `toast`, `about`, `about-version`, `models`, `third-party`, `about-close`. Renamed: `view-drop` → `view-start`, `view-work` → `view-reading`. New: `save` with its `.menu`, `message-title`, the index, the zoom control, the drop veil.
3. **State classes** on `<body>` instead of `.view.active`, plus `mac` or `win` for the key caps.
4. **The index:** built from the document's page breaks and headings; scrolls the reader; marks the part in view.
5. **The Save menu and shortcuts** of section 9, and native menus where pywebview offers them.
6. **Drag-over on any screen** sets `is-dragging`; today only the start screen reacts.
7. **Zoom** by setting `--doc-zoom`; remember nothing between runs unless asked.
8. **"Show in folder"** in the saved toast, through the system (Finder, Explorer). If that is not possible offline-safely, drop the action and keep the toast.
9. **Links** in About and Help open the system browser.
10. **Window:** minimum size 720 × 520.
11. **Messages:** send a title as well as the text, per section 6.
12. **Fonts and licences:** add Noto Sans Hebrew and JetBrains Mono to `THIRD_PARTY_LICENSES.md`.

## 16. Open questions

For the lead:

1. **New Hebrew strings** (`"source": "new"` in `strings.json`) need the owner's review. Strings from the app are unchanged.
2. **The line of formats** under "Open file…" is new and longer than today's; it follows the README's list.
3. **The website address.** The app and its strings say `heocr.github.io`; the newer briefs say `heocr.org`. The mockups use `heocr.org`.
4. **Menus on Windows** depend on what pywebview offers; heocr-app should say.
5. **The pinned Briefcase version** and the MSI image options.

Not verified: today's app was not built or run, so there are no screenshots of it; the renders are from Chromium only, nothing was checked in WebKit; the icons and installer images were not installed on either system; VoiceOver and Narrator were not run.

---

`design[claude/claude-code#shay-macbook-m4]@heocr/opensource`
