# Store graphics

Staged here in the fastlane layout that the repository already uses. They are **not live**: nothing in this folder is read by F-Droid or Play until it is copied over `fastlane/metadata/android/` at the repository root.

```
store/fastlane/metadata/android/
  en-US/images/icon.png                 512 × 512, no transparency
  en-US/images/featureGraphic.png       1024 × 500, no transparency
  en-US/images/phoneScreenshots/1–6.png 1080 × 2400
  iw-IL/images/…                        the same, in Hebrew
```

## When to make them live

- **Screenshots:** with the release that implements this design. They show the designed interface, which the current build does not have yet. Publishing them earlier would show users an app they will not get.
- **Icon and feature graphic:** with the release that carries the new launcher icon, so the listing and the installed app match.

Screenshots 1, 3, 4 and 6 use the interim screens (`01b`, `04b`): Copy only, no Save as Word. When saving ships, re-render them from `01-home` and `04-result` by changing the mockup names in `tools/make_store.py`.

## Screenshots

| # | Screen | English caption | Hebrew caption |
|---|---|---|---|
| 1 | Home | Hebrew text out of any document | טקסט עברי מכל מסמך |
| 2 | Reading | Read on the phone itself | הקריאה נעשית בטלפון עצמו |
| 3 | Result | The text, in reading order | הטקסט, בסדר הקריאה |
| 4 | Result, at a table | Tables are shown as tables | טבלאות מוצגות כטבלאות |
| 5 | About | Nothing leaves the phone | שום דבר לא יוצא מהטלפון |
| 6 | Result at night | In dark mode too | גם במצב כהה |

The captions describe what the screen shows. None makes a claim about accuracy, and the document in them is invented.

## Listing text

`title.txt`, `short_description.txt` and `full_description.txt` are already in the repository for both locales, and they already meet the brief: plain, no claims, no figures. No change is proposed now, so no text files are staged here.

Two edits for later:

1. **When Save as Word ships**, the third "How to use it" bullet becomes:
   - English: `Copy the text, or save it as a Word file (DOCX) or a text file.`
   - Hebrew: `מעתיקים את הטקסט, או שומרים אותו כקובץ וורד (DOCX) או כקובץ טקסט.`
2. **If the listing ever mentions accuracy**, the only permitted wording is that it has not been measured on a held-out set yet. No number.

## Checks

- Feature graphic and icon: PNG, RGB, no alpha channel.
- Screenshots: 1080 × 2400, 24-bit PNG, six per locale (Play accepts 2 to 8).
- The Play icon is under 1 MB (about 7 KB).
- The Hebrew locale folder is `iw-IL`, as in the repository.
