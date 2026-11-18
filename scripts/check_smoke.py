"""Check a smoke report (heocr_desktop --smoke) against expected.json. Exit 1 on any miss."""
import json
import sys
from pathlib import Path


def main(report: str, expected: str) -> int:
    rep = json.loads(Path(report).read_text(encoding="utf-8"))
    exp = json.loads(Path(expected).read_text(encoding="utf-8"))
    print("info:", rep["info"])
    if rep["info"]["tesseract"] != "bundled":
        print("FAIL: the bundled Tesseract was not used")
        return 1
    bad = 0
    got = {f["file"]: f for f in rep["files"]}
    for name, want in exp.items():
        f = got.get(name)
        if not f or "error" in f:
            print(f"FAIL {name}: {f and f.get('error')}")
            bad += 1
            continue
        routes = [r for r, _ in f["routes"]]
        ok = want["route"] in routes
        if "contains" in want:
            ok = ok and all(s in f["text"] for s in want["contains"])
        if "any_of" in want:
            ok = ok and sum(w in f["text"] for w in want["any_of"]) >= want["at_least"]
        print(("ok  " if ok else "FAIL") + f" {name}: routes {routes}, {len(f['text'])} chars")
        bad += not ok
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
