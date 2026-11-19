# Code signing policy

This text also appears, shortened, on the [download page](https://heocr.github.io/download.html) and the [home page](https://heocr.github.io).

## Windows

Free code signing provided by [SignPath.io](https://about.signpath.io), certificate by [SignPath Foundation](https://signpath.org).

- **What is signed:** only the HeOCR desktop installer (`HeOCR-<version>-windows-x64.msi`) and the app's entry point `HeOCR.exe` in it, built from this repository's tagged source by the **Release** workflow on GitHub Actions. Nothing built on a personal computer is signed for Windows.
- **What is not signed with this certificate:** every upstream binary inside the installer, unmodified: for example Python's DLLs, the Microsoft C runtime and WebView2 SDK DLLs, PDFium, and `tesseract.exe` (upstream Tesseract, built by our CI from its pinned source). They keep their publishers' signatures or none.
- **Every signing request is approved by hand**, by an approver below, after checking that the build came from a tagged commit on `main` that passed CI.

## macOS

Signed with the maintainer's Apple Developer ID (`Developer ID Application: Shay Palachy Affek (8X657D2YAU)`), with the hardened runtime, and notarized by Apple. macOS builds are made on the maintainer's Mac by `scripts/release_mac.sh` from the same tagged commit.

## Team roles

| Role | Who |
|---|---|
| Committers and reviewers | Shay Palachy Affek ([@shaypal5](https://github.com/shaypal5)), with AI coding agents (Claude Code) that work through pull requests; every change is reviewed before it merges to `main` |
| Approvers (signing) | Shay Palachy Affek ([@shaypal5](https://github.com/shaypal5)) |

All members use multi-factor authentication on GitHub and SignPath.

## Privacy policy

This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it. In fact HeOCR desktop has no network feature at all: it makes no connections, collects no telemetry or analytics, and checks for no updates.
