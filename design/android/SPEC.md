# HeOCR Android: design specification

The Bounding Box brand, extended to the Android app. This is the implementer's document: what to build, with every size, colour and state. Sizes are in dp; in the WebView one CSS `px` is one dp, so the stylesheets can be read as dp directly.

Designed at 412 × 915 dp, checked at 360 × 800 dp, in light and night, in Hebrew (right to left) and English (left to right). Renders of every screen are in `mockups/png/`.

## 1. Decisions in short

| Question | Decision |
|---|---|
| Native widgets (A) or one WebView screen (B)? | **B.** Every screen is one HTML page in the WebView. Native stays for the system bars, the file picker, the camera, the share sheet and the "save to" picker. |
| Does the design need script in the page? | **No.** Every control is a link or a native `<details>`; the "more actions" sheet opens with a CSS `:target` rule. Section 3 lists what the app has to provide instead. |
| Light or dark? | **The phone's setting decides.** No toggle in the app. |
| Fonts | Noto Sans Hebrew 400/500/700 and JetBrains Mono 500/700, subset and bundled: about 50 KB in total. |
| Launcher icon | Logo 1 on a white ground. A blue-ground alternate is in `launcher/alternate-blue/` for the owner to choose. |
| What ships first | The stylesheet for the result view and the launcher icon need no new app code. Section 2 gives the order. |

## 2. Approach: B, the whole screen in the WebView

**Why B.** The brand is four things: two typefaces, hairlines with a 2 dp radius, the box with its four handles, and the grid band. Toga's Android widgets take a background colour, a text colour and a font size from Pack, and nothing else that matters here: no bundled typeface on a button that I could confirm, no 1 dp outline, no square corner, no pressed-state colour, no icon beside a label, no control over the Material app bar. A screen built that way would be the current screen in blue. In the WebView the same tokens and the same stylesheet draw everything, Hebrew and English mirror with `dir` alone, and the result view, which is already HTML, stops looking like a different app from the buttons above it.

**What B costs.** The page has to tell Python what was tapped, and the app does not have that bridge yet. That is an implementation requirement for heocr-app, listed in section 3; this design does not solve it.

**Order of adoption.** Each step is usable without the next.

1. **Today, no new app code:** replace the `CSS` string in `heocr_mobile/view.py` with `css/result-standalone.css`, put `class="doc"` on `<body>`, and add `font-src data:` to the page's Content-Security-Policy. Swap the launcher icon. The native buttons stay as they are. `mockups/he/result-view-drop-in.html` shows this state.
2. **With the bridge:** move every screen into the WebView (`css/app-standalone.css`), remove the native button rows and the status label, and hide or restyle the app bar (section 6.1).
3. **As they ship:** Save as Word, Save as text and Share. Until then the result screen uses the interim action bar (`04b-result-copy-only`) and the home lede without "Word file" (`01b-home-copy-only`).

## 3. What the app must provide (implementation requirements for heocr-app)

1. **A way for a link in the page to reach Python.** Every action is an ordinary link with an app address, for example `<a href="heocr:photo" role="button">`. The app intercepts the navigation, cancels it and runs the action. The full list is in section 9. In the mockups the real address is in `data-action` and `href` points at the next mockup so the pages can be clicked through.
2. **Fonts inside the page.** The WebView is filled with `set_content("about:blank", html)`, so relative URLs have nothing to resolve against. Use the stylesheets with embedded fonts (`css/*-standalone.css`) and extend the policy to `default-src 'none'; style-src 'unsafe-inline'; font-src data:`. Nothing else in the policy changes. Icons are inline SVG and need no allowance.
3. **Two live values on the reading screen** (page *n* of *m*, elapsed time). Preferred: the app sets them from outside with the WebView's own evaluate-JavaScript call, which needs no script in the HTML. If that is not available, re-render the screen at each page boundary and leave out the elapsed time; the stepping box is a CSS animation and restarts cleanly.
4. **Links to the website open the system browser**, never inside the WebView (the app has no internet permission, so the page would fail anyway).
5. **Back.** System Back goes: sheet open → close the sheet; result, problem or About → home; reading → ask nothing, cancel the reading and go home; home → leave the app.
6. **The WebView reports the system theme** (`prefers-color-scheme`). Android System WebView does this when the app theme is a DayNight theme; verify on a device, and if it does not, set `data-theme="dark"` or `"light"` on `<html>` from the system setting. The tokens support both.
7. **Text zoom.** Leave the WebView's text zoom following the system font scale. The layout was checked at 200% (`mockups/png/font-scale-200/`).
8. **System bars.** Status bar and navigation bar take the page background (`#ffffff` light, `#141414` night) with dark icons in light and light icons in night. Pages already pad for the bottom inset with `env(safe-area-inset-bottom)`.
9. **Saving.** Save as Word and Save as text use the system "save to" picker with a suggested name (the source name with the new extension) and Downloads as the starting folder. After the file is written the app shows the saved toast (section 8.10).

**To verify on a device, not assumed here:** link interception in Toga's Android WebView, the evaluate-JavaScript call under this Content-Security-Policy, `:has()` and `color-mix()` (both need a WebView from 2023 or later; each has a harmless fallback, noted where used), and the VectorDrawable files in `launcher/res/` and `splash/res/`, which were written by hand and not compiled.

## 4. Theme

The app follows the phone's dark setting and has no toggle of its own. On the website light is the default whatever the OS says, because a benchmark page is read once in a browser the reader may not control. A phone app is different: it sits next to every other app, is often opened at night to photograph a letter, and a white screen in a dark phone is the first thing a user notices. Android users set this once for the whole phone and expect apps to obey. The night values are the brand's night palette, unchanged, so the app in the dark looks like the site in night mode.

## 5. Tokens

Colour, type and shape come from the brand's `tokens.json`. `css/tokens.css` holds them with the night values under `prefers-color-scheme: dark`.

| Token | Light | Night | Used for |
|---|---|---|---|
| `--bg` | `#ffffff` | `#141414` | Screen, bars, sheet |
| `--surface` | `#f6f7fc` | `#1c1c1c` | Table header row |
| `--text` | `#0c1222` | `#ecebe8` | Text, icons on controls |
| `--muted` | `#56607a` | `#a29d94` | Secondary text, quiet icons |
| `--line` | `#dfe3f2` | `#2e2d2b` | Hairlines, skeleton lines |
| `--line-strong` | `#b9c1de` | `#4a4844` | Card and table borders, page separators |
| `--accent` | `#2447f9` | `#8fa3ff` | Primary button, the box, links, progress |
| `--accent-soft` | `#eef1ff` | `#1b2040` | Pressed state of quiet controls |
| `--tag` | `#eef0f7` | `#262523` | Chips, notices |
| `--on-accent` | `#ffffff` | `#0b1020` | Text on the primary button |
| `--grid` | `#f1f3fb` | `#1a1a1a` | Grid band lines |
| `--ok`, `--ok-soft` | `#166534`, `#e7f4ec` | `#7fcf9f`, `#18281f` | The "shared from another app" chip only |
| `--no`, `--no-soft` | `#a12a22`, `#fbe9e7` | `#ee9a8b`, `#31201c` | Not used in the app (see 8.11) |

**New for the app** (brand extensions, also listed in section 16):

| Token | Light | Night | Used for |
|---|---|---|---|
| `--control-line` | `#7f8ab0` | `#7a776f` | Border of secondary and framed icon buttons: 3.4:1 and 4.1:1 against the background, where `--line-strong` is under 3:1 |
| `--accent-press` | `#1a36c4` | `#a9b9ff` | Primary button while pressed |
| `--scrim` | `rgba(12,18,34,.36)` | `rgba(0,0,0,.55)` | Behind the sheet |
| `--toast-bg`, `--toast-text`, `--toast-action` | `#0c1222`, `#ffffff`, `#b9c5ff` | `#ecebe8`, `#141414`, `#1a36c4` | Toast |
| `--touch` | 48 | | Smallest touch target |
| `--bar` | 56 | | App bar height |
| `--pad` | 16 | | Screen side padding |
| `--gap` | 12 | | Gap between sibling controls |

### Type

Noto Sans Hebrew carries all Hebrew and all body text in both languages. JetBrains Mono carries the wordmark, English screen titles, figures, file names and small labels. A Hebrew screen title is set in Noto Sans Hebrew, because JetBrains Mono has no Hebrew and its wide space would open gaps between Hebrew words.

| Role | Face, weight | Size / line height |
|---|---|---|
| Screen title (in the box) | Hebrew: Noto Sans Hebrew 700. English: JetBrains Mono 700, tracking −0.03em | 26 / 31 (23 on phones under 380 dp) |
| Section title, problem title | Noto Sans Hebrew 700 | 21 / 27 |
| Capture tile label | Noto Sans Hebrew 700 | 22 / 26 |
| Progress count ("Page 2 of 3") | Noto Sans Hebrew 700 | 20 / 26 |
| Body | Noto Sans Hebrew 400 | 16 / 25 |
| Button label, row title | Noto Sans Hebrew 700 | 16 / 20 |
| Secondary text, hints, notices | Noto Sans Hebrew 400 | 14.5 / 22 |
| Row subtitle, toast detail | Noto Sans Hebrew 400 | 13.5 / 20 |
| Label, chip, page separator | JetBrains Mono 500 | 12 / 17 |
| File name | JetBrains Mono 500 | 14.5 / 20 |
| Figures (time, version, size) | JetBrains Mono 500, tabular | as the text around them |
| Document body | Noto Sans Hebrew 400 | 17 / 29 |
| Document headings | Noto Sans Hebrew 700 | h1 24, h2 20, h3 18, h4–h6 17 |

## 6. Layout

- Side padding 16. Vertical gap between blocks 20 (14 on the result screen).
- Radius 2 everywhere. No shadows, no gradients except the two that draw the grid.
- The grid band sits behind the screen title on Home and About only: lines of `--grid`, 1 dp, every 24 dp, with a hairline under the band.
- Everything uses logical properties (`inline-start`, `inline-end`), so `dir="rtl"` on `<html>` mirrors the screen.
- At 360 dp: screen title 23, capture label 20, scan box padding 20. In the full action bar the primary button loses its icon so "Save as Word" stays on one line.

### 6.1 App bar

56 high, background `--bg`, hairline below, sticky. Two forms:

- **Home, shared file, reading, problem states:** the lockup at the start (mark 30, wordmark JetBrains Mono 700 at 19, `He` in text colour and `OCR` in accent, always left to right), About icon button at the end. The lockup is a link to Home.
- **Result and About:** Back icon button at the start, then the title (the file name in JetBrains Mono 500 at 14, one line, cut with an ellipsis; or "About" in Noto Sans Hebrew 700 at 15), About icon button at the end on the result screen.

The Material app bar that Toga draws today is replaced by this one. If the native bar cannot be removed, set its colour to `--bg`, its title to nothing, and keep this bar below it; do not show two titles.

## 7. Screens and flow

```
            share from another app ──► 2 Received a shared file ─┐
                                                                 ▼
1 Home ── Take a photo / Open a file / Try a sample ──► 3 Reading ──► 4 Result ──► 5 actions
   │                                                       │              │
   └── About (7) ── Copy diagnostics (8)                   └── Cancel     └── Back ──► Home
                                                           │
                                                           └── 6 Problem states ──► one next step
```

| # | Screen | Mockup | Notes |
|---|---|---|---|
| 1 | Home | `01-home` | Grid band with the tagline in the box and a one-sentence lede. The hero is the capture tile (Take a photo): the box with handles, like a viewfinder. Below it Open a file and Try a sample, side by side, equal width. Then two fact rows: the offline promise with the lock icon, and what the app reads. `01b-home-copy-only` is the lede to use until saving ships. |
| 2 | Received a shared file | `02-shared-file` | Title "File received", the file card with a green "Shared from another app" chip, one line saying reading starts right away and the file stays on the phone, then the scan box and progress block already running. Cancel in the bottom bar. No confirmation step: the user chose HeOCR in the share sheet, that was the decision. |
| 3 | Reading | `03-reading` | File card, scan box (hero), "Page 2 of 3" with the elapsed time at the end of the line, one segment per page, a two-line hint that a page can take up to about 20 seconds, Cancel in the bottom bar. Single-page files show "Reading…" in place of the page count and one segment. |
| 4 | Result | `04-result`, full length in `png/full-length/` | Chips (pages, time, "OCR" when OCR was used), the "unread" notice when something was skipped, then the document. Bottom action bar. |
| 5 | Result actions | `04-result`, `05-result-saved`, `05b-result-copied`, `06-result-more` | See 8.9 and 8.10. |
| 6 | Problem states | `07` to `10` | One layout for all four (8.11). |
| 7 | About | `11-about`, full length in `png/full-length/` | Title in the box over the grid band, then Privacy, Accuracy, Version, Licences, Help. |
| 8 | Copy diagnostics | `12-about-diagnostics-copied` | A row in About → Help, and in the result's More sheet. "What is copied?" is a `<details>` under the row. Confirmation is a toast. |

## 8. Components

States are given as default / pressed / disabled / focused. Focus is always a 2 dp outline in `--accent`, offset 2 dp, shown for keyboard and switch access (`:focus-visible`).

### 8.1 Primary button `.btn`
Min height 48, padding 10 × 18, radius 2, background and 1 dp border `--accent`, label `--on-accent` 16/700, optional 24 icon before the label with a 10 gap. Pressed: `--accent-press`. Disabled (`aria-disabled="true"`): background `--tag`, border `--line`, label `--muted`. One primary button per screen.

### 8.2 Secondary button `.btn.secondary`
Same size. Background `--bg`, border `--control-line`, label `--text`. Pressed: background `--accent-soft`, border `--accent`.

### 8.3 Quiet button `.btn.quiet`
No border or background, label `--accent`. Pressed: background `--accent-soft`. Used for the toast action only.

### 8.4 Icon button `.iconbtn`
48 × 48, icon 24 in `--text`, no border; `.framed` adds a 1 dp `--control-line` border (action bar). Pressed: background `--accent-soft`, icon `--accent`. Every icon button has an `aria-label`.

### 8.5 The box
- **Around a title** (`.bb`): 1.5 dp `--accent` outline, 7 dp away from the text, with an 8 dp filled square centred on each corner.
- **Around a hero element** (`.hero`): 1.5 dp `--accent` border with the same four handles, 4 dp outer margin so the handles are not clipped.

Where it appears: the logo, the screen title on Home and About, the capture tile on Home, the scan box on the shared-file and reading screens. Nowhere else: not on buttons, cards, the result or problem states.

### 8.6 Capture tile `a.capture.hero`
The box, min height 27% of the screen height, clamped to 176–260. Centred: camera icon 40 in `--accent`, "Take a photo" 22/700, one muted line 14.5. Pressed: background `--accent-soft`. The whole tile is the touch target.

### 8.7 File card `.file`
1 dp `--line-strong` border, padding 12 × 14, file-type icon 24 in `--muted` (text file, Word document or image), name in JetBrains Mono 500 at 14.5 (wraps anywhere), meta line 13.5 muted: type · pages · size. Not a control.

**Chip** `.chip`: `--tag` background, JetBrains Mono 500 at 12, padding 2 × 8. `.chip.ok` uses `--ok` on `--ok-soft` with a 20 check icon.

### 8.8 Reading: scan box and progress
- **Scan box** `.hero.scan`: min height 250, padding 26. Inside, nine skeleton lines of 8 dp at a 22 dp pitch in `--line`, some shorter, like a page. Lines already "read" are drawn in `--muted`. A small detection box (1.5 dp `--accent`, 8% accent fill, 22 dp high, 8 dp wider than the lines on each side) rests on the current line.
- **Motion:** the box steps down one line every 1.2 s (`steps`, not a glide), and the line it leaves turns dark. After the ninth line it returns to the first. It shows life; it is not a progress measure. With "remove animations" on, the box and lines stand still at the middle.
- **Progress** `.progress`: "Page 2 of 3" 20/700 at the start, elapsed time `0:24` in JetBrains Mono 15 muted at the end. Below, one 6 dp segment per page with 4 dp gaps: done `--accent`, current `--accent` pulsing between 100% and 35% opacity over 1.6 s, to come `--line`. The block is `role="status"` so TalkBack announces each new page; the elapsed time is not announced.
- Calm matters more than precision here: no spinner, no percentage, no estimate of time left.

### 8.9 Result
- **Document** `.doc`: see section 10.
- **OCR marker:** a chip "OCR" in the chips row, and the app's existing note as the first line of the document, set quietly: 13.5 muted with a 2 dp `--line-strong` rule on its start side, no background. It is present whenever OCR was used and never dismissable.
- **"Unread" notice** `.notice`: `--tag` background, warning icon 20 in `--muted`, 14.5 text. Plain words, counted: "1 part wasn't read: a picture on page 3. The rest of the document was read." It sits above the document, below the chips. Not red: nothing failed that the user can fix.
- **Action bar** `.actionbar`: sticky at the bottom, `--bg`, 1 dp `--line-strong` rule above, padding 10 × 12 plus the bottom inset, gap 8. From the start side: **Save as Word** (primary, takes the remaining width, Word-document icon), **Copy**, **Share**, **More** (framed icon buttons, 48 each).
  - Save as Word is first, largest and the only filled control: it is the default.
  - **More** opens the sheet: Save as text (TXT), Copy technical details, Read another document.
  - **Interim bar** (`04b`): until saving and sharing ship, the bar holds one primary button, Copy, full width.
- **Sheet** `.sheet`: fixed to the bottom over a `--scrim`, `--bg`, 1.5 dp `--line-strong` rule on top, a 36 × 3 grip, a mono label, then rows of min height 60 (icon 24 muted, title 16/700, subtitle 13.5 muted). Opens when the page address is `#more`, closes by tapping the scrim or Back. No animation is required; if one is added, 160 ms slide up, ease-out.

### 8.10 Toast (confirmation)
Fixed above the action bar (80 from the bottom; 16 where there is no bar), 12 from each side, min height 48 (56 with an action), `--toast-bg`, text `--toast-text` 14.5, radius 2, check icon at the start. `role="status"`. Leaves after 4 s, or 8 s when it has an action.

| Event | Text | Second line | Action |
|---|---|---|---|
| Saved as Word or text | "Saved to Downloads" (the folder the user picked) | the file name | **Open**, which opens the file in the user's app for that type |
| Text copied | "Text copied" | | |
| Diagnostics copied | "Technical details copied" | "No text from the document. You can paste them into a bug report." | |

Sharing shows no toast: the system share sheet is its own confirmation.

### 8.11 Problem states `.problem`
One layout: the lockup bar, then from the top a 56 dp square frame (1 dp `--line-strong`) holding one 24 icon in `--muted`, the title 21/700 saying what happened, one sentence of body, one muted sentence saying what to do. Pinned to the bottom, within thumb reach: **one primary button with the next step**, and one secondary button.

| State | Icon | Primary | Secondary |
|---|---|---|---|
| File couldn't be read | warning | Choose another file | Back to the first screen |
| Needs a converter (old `.doc`) | Word document | Open the new file | Back to the first screen |
| No text found | camera (or the file icon, for a file) | Take the photo again (or Choose another file) | Open a file |
| Partly done | warning | Show what was read | Read the whole document again |

No red and no error codes on these screens. The file is the problem, not the user, and every state has a way forward. The error code, when there is one, goes into the diagnostics text.

### 8.12 About
Sections are headed by a mono label (12, muted). Privacy: lock icon and the statement. Accuracy: the OCR caution and "The app's accuracy has not been measured on a held-out set yet." No figures appear anywhere in the app. Version: a two-column list, values in JetBrains Mono, left to right. Licences: one row per component with the licence at the end in mono, then a row that opens the full list (the bundled `THIRD_PARTY_LICENSES` text, shown in the same document style). The versions and licences in the mockup are examples; the app fills them from its build. Help: the website row with the "external" icon and the line "The website opens in your browser, outside the app", then Copy technical details.

**What "Copy technical details" copies:** the app, heocr and Tesseract versions; the Android version and phone model; the last file's type, page count and reading time; the error code if there was one. Never the file name, the text or any picture. The `<details>` under the row says exactly this.

## 9. Actions (link addresses)

| Address | Where | The app does |
|---|---|---|
| `heocr:photo` | Home, No text found | Opens the camera |
| `heocr:open` | Home, problem states | Opens the file picker |
| `heocr:sample` | Home | Reads the built-in sample |
| `heocr:cancel` | Shared file, Reading | Stops the reading, goes Home |
| `heocr:home` | Lockup, Back, sheet, problem states | Goes Home |
| `heocr:about` | App bar | Shows About |
| `heocr:save-docx` | Result | Save as Word |
| `heocr:save-txt` | Sheet | Save as text |
| `heocr:copy` | Result | Copies the text, shows the toast |
| `heocr:share` | Result | Opens the system share sheet with the text |
| `heocr:open-saved` | Saved toast | Opens the saved file |
| `heocr:diagnostics` | Sheet, About | Copies the technical details, shows the toast |
| `heocr:licences` | About | Shows the full licence list |
| `heocr:retry` | Partly done | Reads the same file again from the start |
| `heocr:next` | Problem states | The primary step for that state (see 8.11) |
| `#more`, `heocr:dismiss` | Result | Opens and closes the sheet inside the page; the app need not act |
| `https://heocr.github.io` | About | Opens the system browser |

## 10. The result view stylesheet

`css/result.css` styles the HTML that `heocr_desktop/render.py` and `heocr_mobile/view.py` emit today, with no change to the markup: `.block`, `.list-item`, `.label`, `.note-id`, `h1`–`h6.block`, `.table-wrap` with `td.cell` and `td.flagged`, `.figure`, `.page-break`, `h2.section`, `.note`. All rules sit under `.doc`: put the class on `<body>` (today's page) or on the element that wraps the document (the full result screen). The element with `.doc` takes the document's direction, as `view.py` already sets on `<html>`; the app's own chrome takes the interface language.

- **Body:** 17 / 29, paragraphs 14 apart. Headings in the body face, bold.
- **Lists:** each item keeps the label the document had, in bold muted.
- **Tables:** real tables in a 1 dp `--line-strong` frame. Cells do not wrap; a table wider than the screen scrolls sideways inside its own frame and the page never does. First row on `--surface` in bold. `td.flagged` gets the `--tag` background. The scroll frame takes the table's own direction with `:has()`, so an English table in a Hebrew document starts at its first column; without `:has()` it simply starts at the document's start side.
- **Page separator** `.page-break`: mono label ("Page 2") at the start, a `--line-strong` hairline filling the rest of the row, 30 above and 16 below.
- **Headers, footers and notes** `h2.section`: each is a section at the end, opened by a hairline and a 13 muted bold title; the text under it is 15 muted, so it reads as apparatus, not body.
- **Unread picture** `.figure`: a dashed 1 dp frame with the placeholder text centred, 14 muted.
- **App notes** `.note`: see 8.9.

Three files, same rules: `result.css` (needs `tokens.css` and a font stylesheet), `result-standalone.css` (tokens, embedded fonts and the rules in one file, about 76 KB, for today's page), `app-standalone.css` (everything, about 91 KB, for approach B).

## 11. Motion

| What | Motion |
|---|---|
| Scan box | Steps one line every 1.2 s; loop of 10.8 s |
| Current page segment | Opacity 100% → 35% → 100% over 1.6 s |
| Pressed states | Immediate colour change, no transition |
| Sheet, toast | None required. If added: 160 ms, ease-out, slide up 16 dp and fade |
| Between screens | None: the page is replaced |

With the system's "remove animations" setting on (`prefers-reduced-motion`), the scan box and the segment stand still; nothing else moves in the first place.

## 12. Right to left and left to right

- The interface follows the system language: `<html lang="he" dir="rtl">` or `<html lang="en" dir="ltr">`. Nothing else switches.
- Always left to right, isolated with `<bdi dir="ltr">` or `.ltr`/`.num`: the wordmark, versions, sizes, times, licence names, the website address, file extensions.
- A file name is shown with `<bdi>`, so a Hebrew name reads right to left inside an English screen and the other way round.
- The page segments and the progress count run from the start side: in Hebrew the first page is the rightmost segment.
- The document keeps its own direction (section 10).
- Icons that mirror in Hebrew: **Back**, **chevron** and **external link**. All others never mirror: objects (camera, lock, clipboard), file types, check, warning, share, save, copy, close, retry, more. The list with a flag per icon is in `icons/in-app/icons.json`; in the stylesheet an icon mirrors when it has the class `flip`.
- Hebrew punctuation follows the reviewed strings: maqaf (־) after a one-letter prefix before a Latin word, geresh in "שנ׳".

## 13. Accessibility

**Contrast** (WCAG 2.1; AA needs 4.5:1 for text, 3:1 for large text and for the edges of controls):

| Pair | Light | Night |
|---|---|---|
| Text on background | 18.7 | 15.5 |
| Muted text on background | 6.3 | 6.8 |
| Muted text on chip or notice (`--tag`) | 5.5 | 5.7 |
| Accent (links, box) on background | 6.3 | 7.8 |
| Primary button label on accent | 6.3 | 8.0 |
| Primary button label, pressed | 8.9 | 10.0 |
| Green chip text on its ground | 6.3 | 8.3 |
| Toast text on toast | 18.7 | 15.5 |
| Toast action on toast | 11.1 | 7.4 |
| Secondary button border on background | 3.4 | 4.1 |

Hairlines and card borders (`--line`, `--line-strong`) are decoration and carry no information on their own.

**Touch targets.** Every control is at least 48 × 48: buttons (min height 48), icon buttons (48 × 48), rows (min height 60), the capture tile, the `<details>` summary (min height 48), the toast action (48 high). Neighbouring targets are at least 8 apart.

**TalkBack.**

| Element | What it says |
|---|---|
| Lockup | "HeOCR", link to Home |
| Icon buttons | Their `aria-label`: About, Back, Copy, Share, More actions |
| Action links | Announced as buttons (`role="button"`) with their visible label |
| Decorative icons, the scan box, the grip | Hidden (`aria-hidden="true"`) |
| Progress block | `role="status"`: "Page 2 of 3" is announced when it changes |
| Toast | `role="status"`: announced when it appears |
| Sheet | `role="dialog"` with its title; the scrim is labelled "Close" |
| Notices | Read in order, before the document |
| Page separators | Read as "Page 2" |
| Headings | Document headings are real `h1`–`h6`, so heading navigation works in the result |

Colour is never the only signal: the "unread" notice and the problem states have an icon and words, the green chip has a check and words, the current page is also named in text.

**Large text.** At 200% text zoom every screen was rendered and checked (`mockups/png/font-scale-200/`): labels wrap inside their buttons, the action bar grows taller, the two Home buttons stay side by side or wrap to one column, nothing is cut and the page never scrolls sideways. Icons stay at 24.

**Keyboard and switch access.** All controls are links or native elements in document order, so focus order is reading order; focus is visible (section 8).

## 14. Icons

Twenty icons on a 24 dp grid: 2 dp stroke, square ends, mitred corners, no fills except the dots of "more". They are drawn with straight segments wherever the object allows, to sit with the box and its handles. SVG files with `currentColor` are in `icons/in-app/`, with a sheet in `preview.png`.

Asked for in the brief: `camera`, `open-file`, `sample`, `copy`, `share`, `save`, `word-doc`, `text-file`, `info`, `close`, `warning`, `check`, `diagnostics`. Added because the screens needed them: `back`, `chevron`, `more`, `external`, `private`, `image-file`, `retry`.

Icon colour: `--text` on controls, `--muted` beside text, `--accent` only for the camera in the capture tile and inside pressed icon buttons.

## 15. Launcher icon and splash

**Launcher (`launcher/`).** Adaptive icon on the 108 dp canvas: background plain white, foreground Logo 1 at 1 dp per logo unit, centred, so the mark is 41 dp across its handles and its corners sit 29 dp from the centre, inside the 33 dp safe radius. Tested under circle, squircle, rounded-square and teardrop masks on a light and a dark wallpaper: `preview-masks.png`.

- **Icon weight.** For the launcher the logo's strokes are slightly heavier than in the brand files (outline 2.75 instead of 2, handles 7 instead of 6, letter 5 instead of 4.5 on the 48 grid), so the outline survives at 48 px. Same construction, same centre lines.
- **Monochrome layer** for themed icons (Android 13 and later): the whole mark in one colour.
- **Legacy icons** (before Android 8): a white square with a 3 dp radius and a white disc, each with a hairline edge so they hold on a white wallpaper, at 48, 72, 96, 144 and 192 px.
- **Play Store icon:** 512 × 512, no transparency, white ground, mark at 56% of the width.
- **Files:** SVG sources in `svg/`; Android resources in `res/` (VectorDrawable foreground and monochrome, the adaptive-icon XML, the background colour, legacy PNGs); the same PNGs under the names Briefcase reads in `briefcase/` (`heocr-square-*`, `heocr-round-*`, `heocr-adaptive-*`, where the adaptive image is the full 108 dp canvas on white).
- **Alternate:** `alternate-blue/` is the same set with a blue ground and the mark in white. It stands out more on a busy wallpaper and continues the current blue icon; it gives up the two-colour mark. The white ground is the recommendation because it is the logo as approved. This is a taste call for the owner.

**Splash (`splash/`).** The mark alone, centred, on the window background: `#ffffff` light, `#141414` night. On the 288 dp splash canvas the mark is 120 dp wide and its corners sit 85 dp from the centre, inside the 96 dp circle Android masks to. Logo weight, not icon weight, because it is shown large. No wordmark, no animation, no branding image at the bottom. Night uses the night accent and the night text colour. Files: SVG, VectorDrawable for `drawable` and `drawable-night`, colours for `values` and `values-night`, PNGs, square images under Briefcase's names for both themes, and previews at 412 × 915.

## 16. Brand extensions made for the app

Everything here is new relative to the brand handover and should be folded back into the brand guide if the lead agrees.

1. `--control-line`, `--accent-press`, `--scrim` and the three toast colours (section 5).
2. The box on a control: the capture tile is a link and the hero at once. The site only boxes static elements.
3. The scan box animation: the detection box as a moving cursor. The site has no motion.
4. The "icon weight" of the logo for launcher sizes, and the monochrome mark.
5. The in-app icon set and its drawing rules.
6. Hebrew screen titles in Noto Sans Hebrew instead of the display face.
7. The grid at a 24 dp pitch (28 px on the site).
8. Bottom action bar, sheet and toast: components the site does not have, built from the same hairlines, radius and type.
9. The night theme chosen by the system instead of by a toggle.

## 17. Open questions

For the lead:

1. **Hebrew wording.** The strings reused from `MOBILE_STRINGS` and `i18n.py` are unchanged. Every other Hebrew string in `strings/strings.json` is new and needs the maintainer's review; they follow the reviewed style ("וורד", "(DOCX)", maqaf before Latin words).
2. **Licence rows in About** are examples. In particular the licence of HeOCR's own Hebrew model should be taken from the project's records, not from the mockup.
3. **"Open" in the saved toast** needs a viewer app on the phone for `.docx`. If none is installed, drop the action and keep the toast.
4. **Store screenshots** show the designed interface, not the current build. They are staged in `store/` and should go live with the release that implements the design (see `store/README.md`).
5. **Desktop app icons** (`icons/heocr-*.png`, `.icns`, `.ico`) still carry the old aleph. Out of scope here.

Through the lead, for the owner:

6. **Launcher icon ground:** white (recommended) or blue.

---

`design[claude/claude-code#shay-macbook-m4]@heocr/opensource`
