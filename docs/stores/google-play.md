# Google Play: what is ready, and what only the maintainer can do

Status: prepared, nothing submitted. No account is created, nothing is paid, nothing is uploaded until the maintainer does it himself.

## Ready in this repository

- **Store listing**, in English (`en-US`) and Hebrew (`iw-IL`, Play's code for Hebrew), under `fastlane/metadata/android/<locale>/`:
  - title, short description (≤ 80 characters) and full description (≤ 4,000);
  - icon (512 × 512), feature graphic (1024 × 500), three phone screenshots;
  - release notes for versionCode `10000` (0.1.0).
  - CI checks the lengths.
  - The screenshots come from the CI emulator and show only the invented sample page. They show the English UI; Hebrew-UI screenshots are a later addition.
- **Release build:** CI builds `HeOCR-android-release.aab`, the Android App Bundle Play takes (artifact `heocr-android-release`).
  - The bundle is **unsigned** until the upload key exists.
  - Once the four repository secrets below are set, CI signs it with the upload key on `main`, on tags and on manual runs, never in a pull request.
- **Privacy policy:** https://heocr.github.io/privacy.html (heocr.github.io). HeOCR collects no data, and the app has no internet permission.

## Answers for Play Console's forms

| Form | Answer |
|---|---|
| App or game | App. Category: **Productivity** (or Tools) |
| Free or paid | Free. No in-app purchases, no ads |
| Ads | "No, my app does not contain ads" |
| App access | All functionality is available without special access (no login) |
| Content rating (IARC questionnaire) | Reference: utility/productivity. No violence, sexuality, language, controlled substances or gambling. No user-to-user interaction, no sharing of location, no purchases. Expected: Everyone / PEGI 3 |
| Target audience | 18 and over (it is not designed for children; choosing a child age group adds the Families policy) |
| Data safety: does the app collect or share user data? | **No.** The app has no INTERNET permission; documents and photos are read on the device and never transmitted |
| Data safety: encryption in transit | Not applicable (no data is transmitted) |
| Data safety: deletion request | Not applicable (no data is collected); "Data is not collected" |
| Government app, financial features, health | No |
| Permissions declaration | CAMERA only, used when the user taps "Take a photo"; the photo stays on the device |
| Privacy policy URL | https://heocr.github.io/privacy.html |
| Contact email | the maintainer's choice (Play shows it publicly) |

## What only the maintainer can do (identity, payment, agreements, keys)

1. **Create the Play Console developer account.** It is a personal account: HeOCR is not a legal entity, so an organisation account and its D-U-N-S number are out.
   - Pay the one-time **US$25** fee.
   - Complete **identity verification** with a government ID.
   - Accept the Developer Distribution Agreement.
2. **Create the upload key**, once, on his own machine, and keep it backed up. For example:
   ```
   keytool -genkeypair -v -keystore heocr-upload.jks -alias heocr-upload -keyalg RSA -keysize 4096 -validity 10000
   ```
   Then set the four repository secrets in HeOCR/heocr-desktop:
   - `ANDROID_UPLOAD_KEYSTORE_BASE64` (`base64 -i heocr-upload.jks`);
   - `ANDROID_UPLOAD_KEYSTORE_PASSWORD`;
   - `ANDROID_UPLOAD_KEY_ALIAS`;
   - `ANDROID_UPLOAD_KEY_PASSWORD`.

   Agents never see or handle these.
3. **Create the app** in Play Console (package `io.github.heocr.heocr_mobile`) and opt in to **Play App Signing**. Google keeps the app signing key, and the upload key only proves an upload came from HeOCR.
4. **Closed test:** personal accounts created after 13 November 2023 must run one before production.
   - It needs **at least 12 testers opted in for 14 days in a row**, so recruit them first. The HeOCR volunteers are the natural group.
   - Upload the signed AAB to the closed-testing track and share the opt-in link.
5. **Apply for production** after the 14 days, and answer Google's questions about the test.
6. Paste the listing texts and images from `fastlane/metadata/android/`, and fill the forms with the answers above. The agents can prepare a fastlane `supply` run instead, once a Play API service account exists. That account is also the maintainer's to create.

## Versions

- `versionCode` comes from the version in `pyproject.toml`: 0.1.0 → `10000`, 0.1.1 → `10100`.
- Every upload to Play needs a higher one, so each release bumps the version.
