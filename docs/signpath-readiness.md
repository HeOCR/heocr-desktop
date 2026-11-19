# SignPath Foundation readiness

SignPath Foundation signs Windows binaries of open-source projects for free. This is the checklist against its conditions (<https://signpath.org/terms>), and what is left before applying at <https://signpath.org/apply>. The application goes in once the maintainer confirms the form answers; the macOS app is released (v0.1.0, 2026-11-19).

| Condition | Status | Where |
|---|---|---|
| OSI-approved licence, no commercial dual licensing | ✅ Apache-2.0 | `LICENSE` |
| All components open source (OSI) | ✅ with one note: Python's Windows build ships Microsoft's VC++ runtime DLLs (`vcruntime140*.dll`), as every Python on Windows does; the WebView2 runtime is part of Windows | `THIRD_PARTY_LICENSES.md` |
| No malware, no potentially unwanted features | ✅ no network code at all; enforced in-process | `src/heocr_desktop/engine.py`, README "Privacy" |
| The project is maintained and already released in the form to be signed | ⚠️ 0.1.0 is released for macOS; no Windows MSI is published, since nothing goes out unsigned. CI builds and smoke-tests the MSI at every commit (artifact `heocr-windows-msi-unsigned`). The application asks SignPath whether that meets the condition | [Releases](https://github.com/HeOCR/heocr-desktop/releases) |
| Functionality described on the download page | ✅ live | [download page](https://heocr.github.io/download.html) |
| Own binaries built verifiably in CI from source | ✅ the MSI is built on GitHub Actions from the tagged source (Tesseract too, from its pinned upstream source); `release.yml` builds tagged releases | `.github/workflows/` |
| Third-party binaries are not signed with the SignPath certificate | ✅ the signing configuration signs only our MSI and `HeOCR.exe` in it. Upstream binaries stay unmodified and unsigned by us, `tesseract.exe` included: it is upstream Tesseract, though our CI builds it | `docs/code-signing-policy.md` |
| MFA for all team members on GitHub and SignPath | ✅ GitHub: the HeOCR org requires 2FA. ⏳ SignPath: MFA at account creation | — |
| Defined roles: committers/reviewers, approvers | ✅ drafted | `docs/code-signing-policy.md` |
| "Code signing policy" section on the home and download pages, with the SignPath attribution, the team roles and the privacy statement | ✅ live, in both languages | site |
| Manual approval of every signing request | ✅ policy; set in SignPath's project config ("approval required") when the project exists | — |
| Release workflow ready to submit signing requests | ✅ a disabled step in `release.yml` (`signpath/github-action-submit-signing-request`), enabled when `SIGNPATH_ORGANIZATION_ID` is set | `.github/workflows/release.yml` |

Draft form answers are not in this repository; they go to the maintainer for review first.

## Decided with the maintainer

The answers to the open questions (team description, Microsoft binaries, contact) go to the maintainer for confirmation and are not kept here. The scope is decided in this repository: **sign the MSI and `HeOCR.exe` only**. The Microsoft DLLs in the MSI (`vcruntime140*.dll` from CPython's Windows build; the WebView2 SDK's `WebView2Loader.dll` and `Microsoft.Web.WebView2.*.dll`, BSD-3-Clause) already carry Microsoft's signature and are not signed again.

## Order of steps

1. ✅ The macOS app released (v0.1.0); the download page and the code signing policy are live; the org requires 2FA.
2. The maintainer confirms the answers and applies at signpath.org/apply.
3. After approval: the SignPath project with an approval-required policy and an artifact configuration that signs the MSI and `HeOCR.exe`; the repository variables and secret.
4. The next `v*` tag: `release.yml` builds the MSI, SignPath signs it after the maintainer's approval, and the signed MSI goes into a draft release (never a published one). The maintainer publishes it, and the site's Windows button goes live.
