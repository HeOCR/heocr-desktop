# F-Droid submission audit

**Status: official CI container build passed. Submission is still a draft.** Checked 2026-11-20 against [F-Droid's inclusion policy](https://f-droid.org/docs/Inclusion_Policy/), [build metadata reference](https://f-droid.org/docs/Build_Metadata_Reference/), [app developer FAQ](https://f-droid.org/docs/FAQ_-_App_Developers/), [metadata guidance](https://f-droid.org/docs/All_About_Descriptions_Graphics_and_Screenshots/) and [reproducible builds](https://f-droid.org/docs/Reproducible_Builds/). Reviewers decide inclusion. The draft recipe and proposed MR text are in `fdroid/`.

## Inclusion and build blockers

1. **Production build review remains open.** The official Debian CI image built the app and passed its source scan. The runner had network access, used the SDK setup below, and exercised one commit. Verify that the production buildserver supports that SDK setup and can fetch the listed inputs. Prefer Debian tools where compatible and stage required sources through submodules or pinned `srclibs` if needed. Test the tagged release with the buildserver and resolve any new findings. F-Droid's `prebuild` phase is for preparation, while compilation belongs in `build`. [Build metadata reference](https://f-droid.org/docs/Build_Metadata_Reference/#prebuild).
2. **Review the chosen binary sources.** The successful probe used Briefcase from PyPI and Chaquopy's Gradle plugin and runtime from Maven Central. Request review of those exact artifacts and the PyPI wheels under the trusted-source policy. The native build also fetched host tools from upstream releases. Review those separately and use Debian equivalents where feasible. Chaquopy publishes the plugin, runtime and [Android Python build scripts](https://github.com/chaquo/chaquopy/tree/master/target) under MIT. Building those from source would require a separate recipe and is outside this probe.
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

Local validation ran the staging and configuration commands and checked all six PyPI hashes. The successful container build also confirmed the generated Gradle project used the staged wheel directory. See the run evidence below.

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

[Initial run](https://github.com/HeOCR/heocr-desktop/actions/runs/44717180173) pulled the pinned image and installed NDK r27c. It stopped before scanning because `fdroid build --on-server` tried to derive `SOURCE_DATE_EPOCH` before the app checkout existed. The probe now stages the checkout through fdroidserver's VCS code, as the host would before invoking the guest build.

The [second run](https://github.com/HeOCR/heocr-desktop/actions/runs/44717464204) passed the source scan and compiled Tesseract 5.5.3 and its vcpkg libraries with NDK r27c. The executable linked dynamically to the Android system libraries `libc.so`, `libdl.so` and `libm.so`. cibuildwheel downloaded Chaquopy's Python 3.13.15 target archive from Maven Central and then failed before compiling Pillow because the image lacked `cmdline-tools/latest/bin/sdkmanager`. The probe now installs Google's command-line tools 19.0 and provides that path.

On 2026-11-20 the [third run](https://github.com/HeOCR/heocr-desktop/actions/runs/44718184374) built and validated the unsigned release APK for `io.github.heocr.heocr_mobile:20000` (0.2.0) at `359db762880806bdd6d674e4c0f772157a8ec07c`. GitHub required a branch-only launcher because the new manual workflow was still under review. The launcher called the probe workflow from the same checkout. The [log and test metadata](https://github.com/HeOCR/heocr-desktop/actions/runs/44718184374/artifacts/14620153545) record the inputs the job used.

The log's `:app:installReleasePythonRequirements` task shows the actual pip command with `--no-index`, one `Looking in links:` entry for the staged directory, and all seven wheels processed from that directory. The recipe's check for `Looking in indexes:` or `https://chaquo.com/pypi` in the Gradle log passed. PyPI was contacted when staging the six hash-checked wheels and when installing build tools.

### Downloads observed in the successful run

The [per-file inventory](fdroid/buildserver-downloads.tsv) deduplicates the logged download URLs, package origins and filenames. It identifies cases where a filename or SDK revision was matched to its distribution record because the installer did not print the exact URL. The log describes new transfers in this run. Packages already in the pinned image and files bundled inside a wheel, JAR or SDK archive need their own component and licence audit.

| Used for | Observed downloads | Source |
|---|---|---|
| Build environment and input repositories | Official amd64 image, pinned fdroidserver source and HeOCR commit | GitLab Container Registry, GitLab, GitHub |
| Debian host tools | Package indexes and 66 packages or updates, including OpenJDK 21, Python venv/pip, GCC, CMake 3.31.6 and Ninja | Debian Trixie main, updates/security and backports indexes |
| Android SDK and NDK | Platform-tools 37.0.1, command-line tools 19.0, build-tools 31.0.0 and 36.0.0, platform 36 rev. 2, NDK r27c for Tesseract and r27d (27.3.13750724) for Pillow | Google Android SDK repository. F-Droid's SDK manager also fetched transparency checksums and signatures |
| Briefcase and host Python tools | Briefcase 0.4.7, cibuildwheel 4.3.5, their dependencies, and Pillow's wheel-build tools including auditwheel, pkgconf, patchelf and pybind11 | PyPI |
| Native build tools | vcpkg at `9eec002df1cd109f8f104cd966a763daf9751489`, the hash-checked `vcpkg-glibc` bootstrap (2026-09-26) and CMake 4.4.3 selected by vcpkg | Microsoft and Kitware GitHub releases and vcpkg source |
| Native source and models | Tesseract 5.5.3, Leptonica 1.87.0 and the ten other library ports in the table above. Hebrew and English tessdata 4.1.0 | Source archives on GitHub, GitLab (LibTIFF) and SourceForge (GIFLIB). Tesseract model repositories on GitHub |
| Pillow 13.0.0 | Hash-pinned Pillow sdist, native libraries built during this run, and Chaquopy's Python 3.13.15 Android build environment. Wheel SHA-256 `2f420cb4b6db466eef066215bc48691264e07a5f372b82d528e80cfddf183149` | PyPI source, local compilation, and Maven Central for the Python target archive |
| Extra host tools | cibuildwheel's Python Standalone 3.13.18 and virtualenv 21.14.13 zipapp. Briefcase downloaded Temurin JDK 17.0.17+10 because it requires JDK 17 | Astral, PyPA and Adoptium GitHub releases |
| Gradle project and Java dependencies | Briefcase Android template at `0a2b6eb5562b6d435c6ae60351fd5339895c844c`, Gradle 9.5.0, AGP 9.3.1, AndroidX and other Java dependencies | BeeWare GitHub source, Gradle distributions, Google Maven and Maven Central |
| Chaquopy in the app build | Plugin 17.2.0, bootstrap, Java and native runtimes 17.2.0, and Python target 3.13.16-0 with arm64 and standard library archives | Maven Central (`repo.maven.apache.org`) |
| Python app wheels | Six published wheels pinned in `android-pypi-wheels.txt` and the locally built Pillow wheel | PyPI file URLs and local wheel directory |

**fdroidserver findings.** The source scanner reported no errors or warnings. fdroidserver initially warned that r27c was absent, downloaded it and continued. The SDK manager warned that the `latest` alias points to the already recognized 19.0 package. Gradle and CMake emitted deprecation warnings. Gradle's Google Maven lookups for Chaquopy missed and resolved successfully from Maven Central. The source scan runs before the recipe generates the Gradle project, so the log and dependency inventory are needed for those artifacts. The probe did not run an APK binary scan or a production submission review.

## Reproducibility

No bit-for-bit comparison has been performed. CI's release APK is unsigned; its debug APK uses a debug signing key, and any F-Droid-signed APK has a different signature from another signer. Signing differences do not by themselves prevent comparing unsigned payloads. Python/Gradle resolution, generated templates, native build paths and build IDs, NDK and SDK versions, ZIP ordering and embedded timestamps are possible differences, not observed failures. Modern Android Gradle Plugin normalizes some ZIP timestamps; do not assume it normalizes all embedded files. Pin all toolchains and inputs, build twice in independent clean environments, compare hashes and use `diffoscope` to identify differences. F-Droid's signature-copy verification requires matching bytes apart from signatures; an upstream signed APK and a compatible signing arrangement are required for its verified upstream-binary route. A Play AAB upload signature is not a Play-distributed APK signature and does not establish cross-store update compatibility. Aim for reproducibility after obtaining a working server build; it improves independent verification but is not a prerequisite for a normal F-Droid-signed listing.

## Owner submission plan

1. Merge the HeOCR documentation/metadata PR after review; complete the build and dependency blockers above and get owner approval for any new Hebrew text.
2. Choose and publish the Android release tag with owner authorization. Inspect the release APK identity, permissions and notices, then replace all placeholder values in the recipe and changelog.
3. Pin and stage the inputs. Confirm that production can provide the probe's SDK setup or move that setup into the recipe. Test `fdroid readmeta`, `fdroid lint` and a clean `fdroid build --server` on the exact tagged commit. Retain the logs and validate the APK on a device. Verify F-Droid can retrieve the localized metadata from the tag, then test update discovery for the actual tag scheme.
4. Owner forks [fdroiddata](https://gitlab.com/fdroid/fdroiddata), copies the verified recipe to `metadata/io.github.heocr.heocr_mobile.yml` and any required srclib definitions/patches to their conventional locations, then opens an MR using `fdroid/merge-request.md` after replacing placeholders. No MR has been submitted.
5. Respond to reviewer questions, scanner and buildserver results; only enable the build and update checks when verified. Consider reproducible upstream-signed APKs as a follow-up with the owner.
