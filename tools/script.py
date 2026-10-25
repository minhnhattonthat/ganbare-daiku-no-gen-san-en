"""script.py: the editable text, script/<block>.json, one file per text_map block.

    python -X utf8 tools/script.py dump [ROM]   # write/refresh script/*.json from the ROM; never touches a filled `en`

Each file is a JSON list in ROM order, one entry per line: `id` (text_map.sid, stable), `name`, `kind`, `jp` (the ROM
text, decoded), `en` (the translation; "" = not done, the build then keeps `jp`). kind `data` = box-frame art, marks
and empty strings: the build always writes their `jp`, whatever `en` says.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from text_map import BLOCKS, ROM, scan, sid, texts  # noqa: E402

DIR = ROOT / "script"
FILES = {0x1070: "stages", 0x23CEC: "continue", 0x2B4EC: "title", 0x2B643: "ending", 0x2B846: "credits",
         0x2D836: "story", 0x34ACB: "cards"}  # block start -> file name
# not text: ASCII-art box frames (title bubble, menu), the copyright line and TM (already English), empty strings
DATA = {"title10DC", "title10E8", "title10F4", "title145E"}


def block_of(off):
    return next(FILES[lo] for lo, hi, _ in BLOCKS if lo <= off < hi)


def dump(rom):
    items, _ = scan(rom)
    jp = texts(rom, items)
    files = {}
    for it in sorted(i for i in items.values() if i.fmt):
        files.setdefault(block_of(it.off), []).append(it)
    DIR.mkdir(exist_ok=True)
    for name, its in files.items():
        old = {e["id"]: e for e in read(name)}
        rows = []
        for it in its:
            t = jp[sid(it)]
            kind = "data" if it.name in DATA or t == "{end}" else "text"
            rows.append({"id": sid(it), "name": it.name, "kind": kind, "jp": t, "en": old.get(sid(it), {}).get("en", "")})
        lost = [i for i, e in old.items() if e["en"] and i not in {r["id"] for r in rows}]
        if lost:
            raise SystemExit(f"script/{name}.json: translated ids no longer in the ROM: {lost}")
        (DIR / f"{name}.json").write_text(
            "[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n]\n", encoding="utf-8", newline="\n")
        print(f"script/{name}.json: {len(rows)} strings, {sum(bool(r['en']) for r in rows)} translated")


def read(name):
    p = DIR / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else []


def entries():
    """Every script entry, all files."""
    return [e for name in FILES.values() for e in read(name)]


def text():
    """{id: text the build writes}: `en` where filled (kind text), else `jp`."""
    return {e["id"]: e["en"] if e["en"] and e["kind"] == "text" else e["jp"] for e in entries()}


def main():
    if sys.argv[1:2] != ["dump"]:
        sys.exit(__doc__)
    dump(Path(sys.argv[2] if len(sys.argv) > 2 else ROM).read_bytes())


if __name__ == "__main__":
    main()
