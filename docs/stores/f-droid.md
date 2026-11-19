# F-Droid: the recipe, and what submitting needs

Status: prepared, not submitted.

## Ready in this repository

- **Store texts and images** under `fastlane/metadata/android/` (`en-US`, `iw-IL`), the layout F-Droid reads from the source repository. They are the same files Play uses.
- **A draft build recipe**, `docs/stores/fdroid/io.github.heocr.heocr_mobile.yml`, for fdroiddata's `metadata/` folder.
  - It builds the release APK from source the way this repository's CI does: Tesseract and its image libraries from pinned sources (vcpkg), Pillow 13.0.0 against them (cibuildwheel), then Briefcase and Gradle.
  - F-Droid signs the APK with its own key.
  - CI checks it with fdroidserver's `fdroid readmeta` and `fdroid lint` (the `fdroid-metadata` job).
- **The unsigned release APK** is built in CI (artifact `heocr-android-release`): the same form F-Droid's build produces.

## How it fits F-Droid's inclusion policy (https://f-droid.org/docs/Inclusion_Policy/)

- **Apache-2.0, and every component FLOSS.** Chaquopy's Python runtime is MIT, from Maven Central, a trusted Maven repository the policy allows. pypdfium2's PDFium comes as a PyPI wheel; the policy allows prebuilt FLOSS binaries from PyPI. Tesseract, Leptonica and the image libraries are built from source in the recipe.
- **No anti-features:** no ads, no tracking, no network permission, no non-free dependencies.
- **Not yet known:** whether F-Droid's reviewers accept a Briefcase/Chaquopy app as it is. No such app is in F-Droid today that we found, and the build downloads its Python wheels and Gradle dependencies during the build. The merge request is where that gets settled.
- **Not on IzzyOnDroid:** its inclusion policy rejects apps whose code is LLM output, and this app's code is written by AI coding agents. Its 30 MB APK guideline is another obstacle.

## What submitting needs

1. **A GitLab.com account**, the maintainer's own or a HeOCR project one. That's his decision; agents do not create accounts.
2. **A first Android release tag**, `android-v0.1.0`, on the commit to build. A tag is public, so it waits for the maintainer's go.
3. **A merge request to https://gitlab.com/fdroid/fdroiddata**, from a fork, adding the recipe as `metadata/io.github.heocr.heocr_mobile.yml`, titled "New App: io.github.heocr.heocr_mobile".
   - The agents can prepare the branch. Opening the MR is a public action, done on the maintainer's go from his account.
4. **Answering the reviewers' questions.** F-Droid's CI runs the build there; a build too large for their runners is built locally by a reviewer.

**Reproducible builds,** so that F-Droid ships the same signature as Play, come later. They need byte-identical builds from F-Droid's server and ours, and the Chaquopy and Gradle steps do not promise that yet.
