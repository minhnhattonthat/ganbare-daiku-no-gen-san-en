"""batches.py: translator batches from script/*.json, their check, the reviewer pairs file and the merge back.

    python -X utf8 tools/batches.py split            # work/tl/b001.tsv.. + build/terms_<batch>.txt (refuses to overwrite)
    python -X utf8 tools/batches.py check b001       # work/tl/b001.out.tsv: ids, codes, encodable, fit, glossary -> OK
    python -X utf8 tools/batches.py pairs b001       # work/tl/b001.pairs.txt for the reviewer (+-2 context lines)
    python -X utf8 tools/batches.py merge b001 ..    # checked output -> `en` in script/*.json

TSV in: id, speaker, form, limit, jp. In both directions ` / ` = next line of the box, ` // ` = next panel/box of the
same speaker ({page}), {gap} = the ticker's 32-space pause; stage names drop their "1-1 " prefix (merge restores it).
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fit  # noqa: E402
import script  # noqa: E402
from tbl import Table  # noqa: E402

TL = ROOT / "work" / "tl"
SPEAKERS = json.loads((ROOT / "data" / "speakers.json").read_text(encoding="utf-8"))
BATCHES = {  # batch -> name prefixes, in story order
    "b001": ("page", "script"),
    "b002": ("card", "ending", "imm23285", "imm23B60", "imm23E7E", "imm23F1B"),
    "b003": ("credit", "stage"),
}
FORM = {"page": "narration", "ticker": "narration", "card": "menu", "credit": "name", "stage": "name"}
LINE = {"ending": "{nl}{half}", "credit": "{br}{br}"}  # JP/EN line break per box, default {nl}
TABLE = {"stage": "font.tbl", "credit": "jp.tbl"}  # default story_en.tbl
GAP = " " * 32
PREFIX = re.compile(r"^( ?FINAL |\d-\d )")


def box(e):
    return fit.box_of(e["name"])


def entries(batch):
    """Text entries of a batch (no duplicates of identical JP beyond what the game has), story order."""
    pre = BATCHES[batch]
    es = [e for e in script.entries() if e["kind"] == "text" and e["name"].startswith(pre) and box(e)]
    return sorted(es, key=lambda e: next(i for i, p in enumerate(pre) if e["name"].startswith(p)))


def to_tsv(e):
    """Script text -> one-line batch form."""
    t, b = e["jp"].removesuffix("{end}"), box(e)
    t = t.replace("{page}", " // ").replace(LINE.get(b, "{nl}"), " / ").replace("{nl}{half}", " / ")
    t = t.replace("{nl}", " / ").replace("{kana}", "").replace(GAP, "{gap}")
    return PREFIX.sub("", t) if b == "stage" else t


def from_tsv(e, en):
    """Batch English -> script text."""
    b = box(e)
    t = en.replace(" // ", "{page}").replace(" / ", LINE.get(b, "{nl}")).replace("{gap}", GAP)
    if b == "stage":
        t = PREFIX.match(e["jp"]).group(1) + t
    return t + "{end}"


def glossary():
    """[(jp, [en forms])] from the glossary tables, longest JP first."""
    rows = []
    for line in (ROOT / "glossary.md").read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(c) >= 2 and c[0] not in ("JP", "") and not c[0].startswith("-"):
            rows.append((c[0], [re.sub(r"^the ", "", f.strip()) for f in c[1].split(" / ")], line))
    return sorted(rows, key=lambda r: -len(r[0]))


def terms_in(jp):
    """Glossary rows whose JP occurs as a whole term (longer terms mask the shorter ones inside them)."""
    hits = []
    for t, forms, line in glossary():
        if t in jp:
            hits.append((t, forms, line))
            jp = jp.replace(t, "\0")
    return hits


def split():
    TL.mkdir(parents=True, exist_ok=True)
    for batch in BATCHES:
        p = TL / f"{batch}.tsv"
        if p.exists():
            sys.exit(f"{p} exists: delete work/tl/ first to re-split")
        rows = []
        for e in entries(batch):
            w = fit.WINDOWS[box(e)]
            cells = w["cells"] - (4 if box(e) == "stage" else 0)
            limit = f"{cells}x{w['lines']}" + (" // ok" if w["page"] else "") + (" UPPER" if w.get("upper") else "")
            rows.append([e["name"], SPEAKERS.get(e["name"], ""), FORM.get(box(e), "dlg"), limit, to_tsv(e)])
        with p.open("w", encoding="utf-8", newline="\n") as f:
            csv.writer(f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar="\\").writerows(rows)
        terms = {line for e in entries(batch) for _, _, line in terms_in(e["jp"])}
        (ROOT / "build").mkdir(exist_ok=True)
        (ROOT / "build" / f"terms_{batch}.txt").write_text("\n".join(sorted(terms)) + "\n", encoding="utf-8")
        print(f"{p.relative_to(ROOT)}: {len(rows)} entries")


def read_out(batch):
    out = []
    for n, line in enumerate((TL / f"{batch}.out.tsv").read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            name, _, en = line.partition("\t")
            out.append((n, name.strip(), en.strip()))
    return out


def errors(batch):
    es = {e["name"]: e for e in entries(batch)}
    out = read_out(batch)
    errs = []
    names = [n for _, n, _ in out]
    if sorted(names) != sorted(es) or len(set(names)) != len(names):
        errs.append(f"ids: missing {sorted(set(es) - set(names))}, extra {sorted(set(names) - set(es))}, "
                    f"duplicate {sorted({n for n in names if names.count(n) > 1})}")
    tables = {}
    seen = {}
    for n, name, en in out:
        e = es.get(name)
        if e is None:
            continue
        at = f"{name} (line {n})"
        if not en:
            errs.append(f"{at}: empty")
            continue
        if not en.isascii() or "\t" in en or "\\u" in en or not en.isprintable():
            errs.append(f"{at}: non-ASCII, tab or escape")
        if re.sub(r"\{gap\}", "", en).translate(str.maketrans("", "", "{}[]\\")) != re.sub(r"\{gap\}", "", en):
            errs.append(f"{at}: [ ] {{ }} \\ are not in the font (only {{gap}} is a code)")
        if en.count("{gap}") != to_tsv(e).count("{gap}"):
            errs.append(f"{at}: {{gap}} count {en.count('{gap}')} != JP {to_tsv(e).count('{gap}')}")
        text = from_tsv(e, en)
        table = tables.setdefault(box(e), Table.load(ROOT / "tbl" / TABLE.get(box(e), "story_en.tbl")))
        try:
            table.encode(text.replace("{page}", "{nl}"))  # {page} is split off by text_map.layout, not a table code
        except Exception as x:  # noqa: BLE001 - any encode failure is a reportable entry error
            errs.append(f"{at}: not encodable: {x}")
        errs += [f"{at}: {m}" for m in fit.problems(text, box(e))]
        low = en.lower()
        for t, forms, _ in terms_in(e["jp"]):
            if not any(f.lower() in low for f in forms):
                errs.append(f"{at}: glossary {t} -> {' / '.join(forms)} missing")
        key = to_tsv(e)
        if key in seen and seen[key][1] != en:
            errs.append(f"{at}: same JP as {seen[key][0]}, different English")
        seen.setdefault(key, (name, en))
    return errs


def check(batch):
    errs = errors(batch)
    print("\n".join(errs) if errs else "OK")
    return 1 if errs else 0


def pairs(batch):
    es = entries(batch)
    en = {name: t for _, name, t in read_out(batch)}
    lines = []
    for i, e in enumerate(es):
        lines.append(f">> {e['name']} | {SPEAKERS.get(e['name'], '')} | {to_tsv(e)}\n   EN: {en.get(e['name'], '')}")
    p = TL / f"{batch}.pairs.txt"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{p.relative_to(ROOT)}: {len(lines)} pairs (entries are in story order: read neighbours for context)")


def merge(batch):
    if errors(batch):
        return check(batch)
    en = {name: t for _, name, t in read_out(batch)}
    for name in script.FILES.values():
        rows = script.read(name)
        for r in rows:
            if r["name"] in en and r["kind"] == "text":
                r["en"] = from_tsv(r, en[r["name"]])
        script.write(name, rows)
    print(f"merged {len(en)} entries of {batch}")
    return 0


def main():
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("", [])
    if cmd == "split":
        return split()
    if cmd in ("check", "pairs", "merge") and args:
        return max((globals()[cmd](b) or 0) for b in args)
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
