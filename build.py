"""build.py: build/gensan_en.sfc from the pinned dump (rom.sha1) and the text.

    python -X utf8 build.py            # script/*.json: `en` where filled, else `jp`
    python -X utf8 build.py --marker   # every text entry -> "(n)" + a digit ruler per line (markers.txt: n -> id)
    python -X utf8 build.py --out F    # write F (and writes.txt, markers.txt beside it) instead of build/

The ROM is expanded to 2 MiB and patched by tools/engine.py (half-width story font, stage-name hook); every text
block moves to the expanded banks. Every write is logged to build/writes.txt and checked with romdiff (no byte changes
outside a logged write, and each write found the original bytes it expected).
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402
import engine  # noqa: E402
import romdiff  # noqa: E402
import script  # noqa: E402
from text_map import ROM, layout, scan, texts  # noqa: E402

OUT = ROOT / "build" / "gensan_en.sfc"
# title-screen bubble, vertical kana laid out as ASCII art: no marker (redrawn with the title graphics)
NO_MARKER = {"title10E2", "title10EE"}
PAGE_DEMO = {"script3.2", "ending1.2"}  # markers that also get a second panel/box ({page}), to see the split work
# glyph torture lines: every character the English tables have, double spaces included
TORTURE = {
    "page2": "(39) !\"#$%&'()*+,-./0123{nl}456789:;<=>?@ABCDEFGHIJ{nl}KLMNOPQRSTUVWXYZ^_`abcd{nl}efghijklmnopqrstuvwxyz|~{end}",
    "credit0": "(20)ABCDEFGHIJKLMNOPQRSTUVW{br}{br}XYZ 0123456789 !\"%&'()*+,-./:;=?{end}",
}
TOKEN = re.compile(r"\{[^}]*\}|\[[0-9A-F]{2}\]")


def ruler(n, start=0):
    return "".join(str((start + k + 1) % 10) for k in range(n))


def marker(e, n):
    """Same lines as the Japanese, each a digit ruler (the last digit seen = the column it reached), the first one
    starting with (n). Story lines get 2 rulers cells per glyph (half-width) plus 4 to show the clip."""
    jp, fmt = e["jp"], e["id"][0]
    sep = "{nl}" if fmt == "D" else "{br}"
    lines = []
    for k, line in enumerate(jp.removesuffix("{end}").split(sep)):
        lead = "{half}" if line.startswith("{half}") else ""
        glyphs = len(TOKEN.sub("", line).rstrip())
        if fmt == "B":
            lines.append(line[:4] + f"({n})" + ruler(20, 4 + len(str(n)) + 2))
        elif not glyphs:
            lines.append(lead)
        else:
            width = 2 * glyphs + 4 if fmt == "D" else 30
            tag = f"({n})" if not k else ""
            lines.append(lead + tag + ruler(width - len(tag), len(tag)))
    page = f"{{page}}({n}b)" + ruler(10, 4 + len(str(n))) if e["name"] in PAGE_DEMO else ""
    return sep.join(lines) + page + "{end}"


def main():
    global OUT
    if "--out" in sys.argv:
        OUT = Path(sys.argv[sys.argv.index("--out") + 1]).resolve()
    check_rom.check()
    rom = ROM.read_bytes()
    big = engine.expand(rom)
    items, refs = scan(rom)
    text = texts(rom, items) | script.text()
    en = {e["id"] for e in script.entries() if e["en"] and e["kind"] == "text"}
    if "--marker" in sys.argv:
        marked = [e for e in script.entries() if e["kind"] == "text" and e["name"] not in NO_MARKER]
        text |= {e["id"]: TORTURE.get(e["name"]) or marker(e, n) for n, e in enumerate(marked)}
        en = {e["id"] for e in marked}
        OUT.parent.mkdir(exist_ok=True)
        (OUT.parent / "markers.txt").write_text(
            "".join(f"{n} {e['id']} {e['name']}\n" for n, e in enumerate(marked)), encoding="utf-8")
    out, writes = layout(big, items, refs, text, en, engine.MOVES)
    out, more = engine.apply(out)
    writes = sorted(writes + more)
    errs, _ = romdiff.check(rom, out, set(), writes)
    if errs:
        sys.exit("\n".join(errs))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(out)
    (OUT.parent / "writes.txt").write_text(
        "".join(f"{o:06X} {a.hex()} {b.hex()} {n}\n" for o, a, b, n in writes if a != b), encoding="utf-8")
    print(f"{OUT} sha1 {hashlib.sha1(out).hexdigest()} ({len(en)} strings in English)")


if __name__ == "__main__":
    main()
