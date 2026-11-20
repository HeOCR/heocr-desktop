# F-Droid submission audit

**Status: blocked, draft only, not submitted.** Checked 2026-11-20 against [F-Droid's inclusion policy](https://f-droid.org/docs/Inclusion_Policy/), [build metadata reference](https://f-droid.org/docs/Build_Metadata_Reference/), [app developer FAQ](https://f-droid.org/docs/FAQ_-_App_Developers/), [metadata guidance](https://f-droid.org/docs/All_About_Descriptions_Graphics_and_Screenshots/) and [reproducible builds](https://f-droid.org/docs/Reproducible_Builds/). Reviewers decide inclusion; lint is not a build or a policy approval. The draft recipe and proposed MR text are in `fdroid/`.

## Inclusion and build blockers

1. **No verified F-Droid build.** CI builds on Ubuntu, not the F-Droid Debian buildserver. The recipe installs Briefcase with pip and then invokes scripts which clone vcpkg, bootstrap it, fetch source archives and traineddata, install cibuildwheel, and resolve Gradle and Python packages. These downloads may fail under buildserver network, scanner, resource or dependency constraints. The script can use as many jobs as CPUs. Inventory every URL, hash, transitive dependency and executable bootstrap; replace untrusted binary bootstraps with Debian/source-built tools, use pinned sources and Debian packages where possible, and arrange sources through submodules or pinned `srclibs`. Adapt scripts to use staged inputs instead of unconditional network fetching. Run `fdroid build --server` and resolve scanner findings with reviewers; do not blanket `scanignore` them. A 25-minute GitHub build does not establish server feasibility. `prebuild` is for preparation, while compilation belongs in `build` ([reference](https://f-droid.org/docs/Build_Metadata_Reference/#prebuild)).
2. **Chaquopy and Briefcase source builds are not established on that server.** Briefcase 0.4.7 is installed as a PyPI tool; it generates a Gradle project and its template resolves Chaquopy 17.2.0 from Maven. Chaquopy's MIT-licensed [source](https://github.com/chaquo/chaquopy) includes the plugin, runtime and [Android Python build scripts](https://github.com/chaquo/chaquopy/tree/master/target); that demonstrates a source route, not a tested F-Droid build. Pin source revisions for Briefcase, its Android template, Chaquopy and CPython and their build dependencies; stage them with submodules or new pinned srclib definitions as needed, build the plugin/runtime and target Python into a local Maven repository, and point generated Gradle at it. Audit whether that path fits server tools and limits. Alternatively ask reviewers whether the exact FLOSS Maven artifacts and PyPI tool/wheels qualify for the policy's conditional trusted-source exceptions. There is no demonstrated turnkey all-source recipe or reviewer acceptance yet.
3. **Binary and licence inventory is incomplete for Android.** The existing `THIRD_PARTY_LICENSES.md` is based on desktop artifacts with an Android supplement, not an exhaustive inspection of the resolved Android APK or build toolchain. Resolve and record every transitive Gradle, Python, native and Python-runtime dependency, version, source, binary origin, hash and licence; inspect generated APK, wheel and Maven contents and publish the complete Android bill of materials and licence notices. In particular establish the origin and licence of every PDFium subcomponent and CPython support library, AndroidX/AppCompat and Gradle transitive artifacts, Toga dependencies, and build-only tooling. Verify source and redistribution rights for both HeOCR models and the two pinned tessdata files. Until this is done, an assertion that **every** dependency is FLOSS would be premature.
4. **Release identity is a placeholder.** The draft's `android-v0.1.0`, 0.1.0 and 10000 are not verified release facts: the app config currently says 0.2.0 and no `android-v*` tag was found on 2026-11-20. The build entry is disabled and automatic updates disabled to prevent treating it as ready. Owner must select and publish a real immutable release tag after review, verify APK application ID, versionName and versionCode with `aapt`/`apkanalyzer`, update recipe and matching changelog name, and test tag discovery before enabling updates. Do not create a tag without owner authorization.
5. **Policy age / functionality review.** The policy generally requires three months of active development unless an exception applies, and a functional app consistent with its listing. Verify dates from full history and eligibility or document an exception; the shallow checkout cannot establish age. Confirm Android release functionality and translations with the owner. Existing Hebrew is unchanged; any new Hebrew store text requires owner approval.

## Known components and provenance

This is an inventory of *identified* dependencies, not an exhaustive proof. `THIRD_PARTY_LICENSES.md`, `pyproject.toml`, `tesseract/pins.json`, `tesseract/vcpkg.json`, and the build scripts are the current source records. Versions below describe declared inputs, not a verified APK manifest.

| Component | Declared licence | Android origin / remaining check |
|---|---|---|
| HeOCR app and heocr 0.2.0 | Apache-2.0 | App source and PyPI package. |
| HeOCR OCR models `heocr_modern_v1` and `heocr_oldprint_v1` | Apache-2.0 | Both ship in the heocr 0.2.0 wheel with their notices. The Android app uses `heocr_modern_v1` by default. [Modern model](https://doi.org/10.5281/zenodo.24372349), [old print model](https://doi.org/10.5281/zenodo.24372352). |
| pypdfium2 5.15.2 and PDFium | Apache-2.0 OR BSD-3-Clause; PDFium BSD-3-Clause | PyPI wheel contains native prebuilt PDFium and many subcomponents, including FreeType (FTL), HarfBuzz (MIT), ICU (Unicode-3.0), image libraries and LLVM pieces. Audit exact wheel and all nested licences/sources. PyPI wheels are *potentially* acceptable, not automatically approved. |
| Pillow 13.0.0 | HPND/MIT-CMU | Source sdist, built for Android by cibuildwheel; statically links selected vcpkg image libraries. Audit its actual binary, build inputs and notices. |
| defusedxml 0.7.1 | PSF-2.0 | PyPI; inspect resolved package and transitive dependencies. |
| Toga core, Toga Android and Travertino 0.5.7 | BSD-3-Clause | PyPI wheels. Toga Android declares Toga Core, which declares Travertino. Audit the separate Gradle dependencies. |
| Chaquopy 17.2.0 | MIT | Plugin/runtime via Maven Central; target Python and native support binaries require component-level source/licence verification. CPython is PSF-2.0; its bundled libraries have separate licences. Maven provenance alone does not establish all embedded component licences. |
| Tesseract 5.5.3 | Apache-2.0 | Compiled from a hash-checked source tarball and packaged as `libtesseract_exec.so`. See the native build inventory below for Leptonica and its dependencies. |
| tessdata_best Hebrew / tessdata_fast English 4.1.0 | Apache-2.0 | Prebuilt traineddata downloaded by hash; check source, licensing and reviewers' treatment of model assets. |
| Noto Sans Hebrew, JetBrains Mono | OFL-1.1 | Bundled font subsets; licence texts in `third_party/fonts`. |
| Briefcase 0.4.7, cibuildwheel, vcpkg, Gradle, JDK, Android SDK/NDK and transitive build dependencies | Multiple licences; inventory outstanding | Build tools and downloads must themselves satisfy the FLOSS toolchain policy; verify exact versions, sources and licences, including vcpkg bootstrap. Use Debian OpenJDK, not Oracle JDK. |

The policy conditionally allows FLOSS Maven binaries, PyPI wheels and official Android SDK prebuilts, and prefers Debian packages when possible. The full Gradle, Python runtime and host build tool inventories remain open.

### Android wheel sources

The [Android CI log](https://github.com/HeOCR/heocr-desktop/actions/runs/44695668188) shows Chaquopy pip searching both PyPI and `https://chaquo.com/pypi-13.1`. The log names the selected wheels but does not establish the origin of cached downloads. Chaquopy's separate wheel index is outside F-Droid's listed trusted binary sources. Its Maven Central artifacts are a separate review question.

The F-Droid recipe stages the six release wheels seen in CI (heocr, pypdfium2 for Android arm64, defusedxml, toga-android, toga-core and travertino) using exact PyPI file URLs and SHA-256 hashes in [android-pypi-wheels.txt](fdroid/android-pypi-wheels.txt). The seventh wheel, Pillow, is compiled in the recipe from the hash-pinned PyPI sdist. The recipe logs the wheel source list, Pillow's `BUILD_INFO-pillow.json` and the SHA-256 of every staged wheel. Refresh these inputs when changing the app's Python dependencies or Android ABI.

Chaquopy 17.2.0 adds its extra index only when the pip options lack an explicit `--index-url` or `-i` token. The recipe passes `--index-url https://pypi.org/simple` as separate tokens and uses `--no-index` to disable index lookups altogether. A missing transitive dependency must be added with provenance before the build can pass. This applies to the app wheels. Briefcase, cibuildwheel and their host-side dependencies still require a separate toolchain review. [Chaquopy 17.2.0 pip implementation](https://github.com/chaquo/chaquopy/blob/17.2.0/product/gradle-plugin/src/main/python/chaquopy/pip_install.py).

Local validation ran the recipe's staging and configuration commands and checked all six PyPI hashes. A pip dry run for Android arm64 and CPython 3.13 resolved all seven app wheels from the staged directory using the Pillow wheel from CI. The F-Droid buildserver test still needs to confirm the generated Gradle project uses those options.

### vcpkg libraries from the Android build

The [`tesseract-android-arm64` CI artifact](https://github.com/HeOCR/heocr-desktop/actions/runs/44711765760/artifacts/14616828960) includes the source pin, static archives and port licence files. These are the library ports identified by its `licenses/` files, paired with the static archives present in `deps/lib/`. This records the inputs available to the linker. Confirm the linked objects separately when inspecting the final APK.

| vcpkg port | Static archives in the CI artifact | Licence for the library |
|---|---|---|
| `cpu-features` | `libcpu_features.a`, `libndk_compat.a` | Apache-2.0 |
| `giflib` | `libgif.a` | MIT |
| `leptonica` | `libleptonica.a` | Leptonica BSD-style |
| `libjpeg-turbo` | `libjpeg.a`, `libturbojpeg.a` | IJG, BSD-3-Clause and zlib |
| `liblzma` | `liblzma.a` | 0BSD for the library |
| `libpng` | `libpng.a`, `libpng16.a` | PNG-2.0 |
| `libspng` | `libspng_static.a` | BSD-2-Clause |
| `libwebp` | `libsharpyuv.a`, `libwebp.a`, `libwebpdecoder.a`, `libwebpdemux.a`, `libwebpmux.a` | BSD-3-Clause |
| `openjpeg` | `libopenjp2.a` | BSD-2-Clause |
| `tiff` | `libtiff.a` | LibTIFF licence |
| `zlib` | `libz.a` | zlib |

`BUILD_INFO.json` records vcpkg commit `9eec002df1cd109f8f104cd966a763daf9751489`, Android API 24 and NDK `30.0.16248370`. Its `vcpkg_ports` field also lists these entries from the install's `share/` directory: `CpuFeatures`, `CpuFeaturesNdkCompat`, `WebP`, `doc`, `gif`, `jpeg`, `man`, `png`, `spng`. Those entries do not represent additional library archives. The draft selects NDK r27c, so confirm the build and library inventory with the actual F-Droid toolchain before submission.

## IzzyOnDroid decision

HeOCR is pursuing F-Droid and Google Play. [IzzyOnDroid's inclusion policy](https://izzyondroid.org/docs/general/AppInclusionPolicy/), checked 2026-11-20, rejects apps written with LLMs, which applies to this app. Its usual APK limit of 30 MB is a second concern. The [Android preview 5 APK](https://github.com/HeOCR/heocr-desktop/releases/tag/android-preview-5) is 40,834,631 bytes, about 39 MiB.

## Network and anti-features

App configuration removes INTERNET and ACCESS_NETWORK_STATE; CI inspects the generated manifest. The desktop engine installs an offline socket guard and the build disables Tesseract curl/archive; this is evidence of intent, not an independent audit of every Android runtime path. Verify the final merged manifest and perform on-device network tests. Build-time downloads are separate from app runtime behavior. No ads, telemetry, proprietary service or other anti-feature has been identified in the reviewed configuration; final dependency and behavior review remains open. Do not add an `AntiFeatures` entry without evidence; F-Droid reviewers make the final classification.

## Metadata validation

On 2026-11-20, fdroidserver 2.4.5 installed from PyPI in a temporary Python 3.12 venv successfully ran `fdroid readmeta` and `fdroid lint io.github.heocr.heocr_mobile` against this YAML with a sparse checkout of fdroiddata's `config/`. Both warned that apksigner was absent and the temporary config permissions were loose; neither signs or builds an APK. The fdroidserver source-metadata importer read en-US and iw-IL titles, summaries, descriptions, changelogs and images. Independent length checks found titles 5/5, summaries 74/69, descriptions 984/885 and changelogs 163/149 characters respectively (excluding final newline); all fit the published 50/80/4000/500 limits. All ten PNGs decoded. Changelogs refer to placeholder code 10000, so rename them after the real code is verified. These checks do not establish translation quality or a successful full F-Droid update/build.

## Buildserver probe

Run **F-Droid buildserver probe** from GitHub Actions or use `gh workflow run fdroid-buildserver.yml --ref <branch>` once the workflow is on main. It tests the checkout's commit and Android version using a temporary copy of the draft recipe. It invokes `fdroid build --on-server --test` with scanning enabled inside the same Debian image used by [fdroiddata's build job](https://gitlab.com/fdroid/fdroiddata/-/blob/master/.gitlab-ci.yml). This exercises the container build path. F-Droid's production VM and publication checks remain for the submission.

- Image: `registry.gitlab.com/fdroid/fdroidserver:buildserver-trixie@sha256:1ea8bef1820bff06c2974e31b4fc4c79c364cd24231b86e71fa4b926797e0dac` (linux/amd64).
- fdroidserver revision: `8f52ae3ce287bc28964db544b970b88dce9c38bf`, the revision in the image label.
- Evidence: the run's `fdroid-buildserver-evidence` artifact holds the build log and the exact test metadata. A successful recipe must log Chaquopy's staged wheel directory and pass the check for an unexpected index in Gradle's log.

## Reproducibility

No bit-for-bit comparison has been performed. CI's release APK is unsigned; its debug APK uses a debug signing key, and any F-Droid-signed APK has a different signature from another signer. Signing differences do not by themselves prevent comparing unsigned payloads. Python/Gradle resolution, generated templates, native build paths and build IDs, NDK and SDK versions, ZIP ordering and embedded timestamps are possible differences, not observed failures. Modern Android Gradle Plugin normalizes some ZIP timestamps; do not assume it normalizes all embedded files. Pin all toolchains and inputs, build twice in independent clean environments, compare hashes and use `diffoscope` to identify differences. F-Droid's signature-copy verification requires matching bytes apart from signatures; an upstream signed APK and a compatible signing arrangement are required for its verified upstream-binary route. A Play AAB upload signature is not a Play-distributed APK signature and does not establish cross-store update compatibility. Aim for reproducibility after obtaining a working server build; it improves independent verification but is not a prerequisite for a normal F-Droid-signed listing.

## Owner submission plan

1. Merge the HeOCR documentation/metadata PR after review; complete the build and dependency blockers above and get owner approval for any new Hebrew text.
2. Choose and publish the Android release tag with owner authorization. Inspect the release APK identity, permissions and notices, then replace all placeholder values in the recipe and changelog.
3. Pin/stage inputs, test `fdroid readmeta`, `fdroid lint` and a clean `fdroid build --server` on the exact tagged commit; retain logs and validate the APK on a device. Correct `sudo`, NDK, SDK/JDK and output paths against that build. Verify F-Droid can retrieve the localized metadata from the tag. Decide and test update-check mode for the actual tag scheme.
4. Owner forks [fdroiddata](https://gitlab.com/fdroid/fdroiddata), copies the verified recipe to `metadata/io.github.heocr.heocr_mobile.yml` and any required srclib definitions/patches to their conventional locations, then opens an MR using `fdroid/merge-request.md` after replacing placeholders. No MR has been submitted.
5. Respond to reviewer questions, scanner and buildserver results; only enable the build and update checks when verified. Consider reproducible upstream-signed APKs as a follow-up with the owner.
