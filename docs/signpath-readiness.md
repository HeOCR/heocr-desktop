# SignPath Foundation readiness

SignPath Foundation signs Windows binaries of open-source projects for free. This is the checklist against its conditions (<https://signpath.org/terms>), and what is left before applying at <https://signpath.org/apply>. The application goes in only after the first public preview release exists, and only after the maintainer approves the form answers.

| Condition | Status | Where |
|---|---|---|
| OSI-approved licence, no commercial dual licensing | ✅ Apache-2.0 | `LICENSE` |
| All components open source (OSI) | ✅ with one note: Python's Windows build ships Microsoft's VC++ runtime DLLs (`vcruntime140*.dll`), as every Python on Windows does; the WebView2 runtime is part of Windows | `THIRD_PARTY_LICENSES.md` |
| No malware, no potentially unwanted features | ✅ no network code at all; enforced in-process | `src/heocr_desktop/engine.py`, README "Privacy" |
| The project is maintained and already released in the form to be signed | ⏳ needs the first public preview release (MSI on GitHub Releases), after the gate verdict and the maintainer's go | Releases |
| Functionality described on the download page | ⏳ in heocr.github.io PR (download page), not merged | `download.html` |
| Own binaries built verifiably in CI from source | ✅ the MSI and Tesseract are built on GitHub Actions from pinned sources; `release.yml` builds tagged releases | `.github/workflows/` |
| Third-party binaries are not signed with the SignPath certificate | ✅ the signing configuration will sign only our MSI and `HeOCR.exe`, `tesseract.exe` | `docs/code-signing-policy.md` |
| MFA for all team members on GitHub and SignPath | ⏳ the maintainer confirms GitHub MFA; SignPath MFA at account creation | — |
| Defined roles: committers/reviewers, approvers | ✅ drafted | `docs/code-signing-policy.md` |
| "Code signing policy" section on the home and download pages, with the SignPath attribution, the team roles and the privacy statement | ⏳ in the heocr.github.io PR, not merged | site |
| Manual approval of every signing request | ✅ policy; set in SignPath's project config ("approval required") when the project exists | — |
| Release workflow ready to submit signing requests | ✅ a disabled step in `release.yml` (`signpath/github-action-submit-signing-request`), enabled when `SIGNPATH_ORGANIZATION_ID` is set | `.github/workflows/release.yml` |

Draft form answers are not in this repository; they go to the maintainer for review first.
