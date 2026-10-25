"""fit.py: does an English line fit its box? Budgets per box variant are in data/windows.json (measured in the marker
build, phase 5: cells per line = letters, since every font here is fixed-width; lines per box).

    python -X utf8 tools/fit.py                      # lint every filled `en` in script/: exit 1 on any overflow
    python -X utf8 tools/fit.py "text{nl}more" --box panel   # dry run for translators: cells per line vs budget

Box of an entry: the first `match` prefix in windows.json that its `name` starts with. A line is a {nl} (story) or
{br} (8x8 text) piece; {half} and other control codes take no cell.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
WINDOWS = json.loads((ROOT / "data" / "windows.json").read_text(encoding="utf-8"))
TOKEN = re.compile(r"\{[^}]*\}")


def box_of(name):
    return next((k for k, w in WINDOWS.items() for m in w["match"] if name.startswith(m)), None)


def lines(text):
    body = text.removesuffix("{end}")
    return [TOKEN.sub("", s) for s in re.split(r"\{nl\}|\{br\}", body)]


def problems(text, box):
    """Overflow messages for `text` in `box` ({page} parts are checked as separate boxes)."""
    w, out = WINDOWS[box], []
    pages = text.removesuffix("{end}").split("{page}")
    if len(pages) > 1 and not w["page"]:
        out.append("{page} only works in panels and ending boxes")
    for p, part in enumerate(pages):
        at = f"page {p + 1} " if len(pages) > 1 else ""
        ls = lines(part)
        if len(ls) > w["lines"]:
            out.append(f"{at}{len(ls)} lines > {w['lines']}")
        for k, s in enumerate(ls):
            if len(s) > w["cells"]:
                out.append(f"{at}line {k + 1}: {len(s)} cells > {w['cells']}: {s!r}")
        if w.get("upper") and any(c.islower() for c in "".join(ls)):
            out.append(f"{at}lowercase in an 8x8 (uppercase-only) font")
    return out


def lint():
    import script
    bad = 0
    for e in script.entries():
        if not e["en"] or e["kind"] != "text":
            continue
        box = box_of(e["name"])
        errs = [f"no box for {e['name']} in data/windows.json"] if box is None else problems(e["en"], box)
        for m in errs:
            print(f"{e['id']} {e['name']}: {m}")
        bad += bool(errs)
    print(f"{bad} entries over budget" if bad else "fit: all filled entries fit")
    return 1 if bad else 0


def main():
    if len(sys.argv) > 1:
        box = sys.argv[sys.argv.index("--box") + 1]
        text = sys.argv[1]
        for p, part in enumerate(text.removesuffix("{end}").split("{page}")):
            print(f"-- page {p + 1}" if p else "", end="\n" if p else "")
            for s in lines(part):
                print(f"{len(s):3} {s}")
        errs = problems(text, box)
        print("\n".join(errs) if errs else f"fits {box}")
        return 1 if errs else 0
    return lint()


if __name__ == "__main__":
    sys.exit(main())
