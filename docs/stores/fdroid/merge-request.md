# Draft only — owner to complete and submit

Title: New App: io.github.heocr.heocr_mobile

HeOCR extracts Hebrew text from documents and images on the device. The Android app is Apache-2.0 and the source is https://github.com/HeOCR/heocr-desktop. Its fastlane metadata is in the source tree. It requests no Internet permission; OCR models and Tesseract are bundled. No anti-features have been identified in the current review.

This proposal is **not ready to submit**. Replace this paragraph after resolving the audit in `docs/stores/f-droid.md` and provide:

- Released tag and exact commit: [owner to fill]; APK version name/code and application ID: [verified values].
- Buildserver test and scanner results: [commands, version and outcome]. List required srclibs, patches, network inputs and binary exceptions, with hashes, sources and licences.
- Full Android runtime and build dependency licence/provenance inventory: [link]. Include the release wheel URLs and hashes, locally built Pillow record and build log showing Chaquopy resolving from the staged wheels with indexes disabled. Explain the separate Chaquopy Maven/Python artifacts, PDFium wheel, vcpkg bootstrap and traineddata treatment.
- Fastlane validation and age/eligibility evidence: [results].
- Known limitations and reviewer questions: [details].

The accompanying YAML is an experimental, disabled placeholder; do not submit it as a working recipe. This draft does not request reproducible upstream-signed binaries. F-Droid's normal signing is assumed pending maintainer decision.
