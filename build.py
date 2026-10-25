"""build.py: build/gensan_en.sfc from the pinned dump (rom.sha1) and the text.

    python -X utf8 build.py

Text source: the ROM's own strings until phase 4 adds script/, so today this is the identity build and must print
"identical". Every write is logged to build/writes.txt and checked with romdiff (no byte changes outside a logged
write, and each write found the original bytes it expected).
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402
import romdiff  # noqa: E402
from text_map import ROM, layout, scan, texts  # noqa: E402

OUT = ROOT / "build" / "gensan_en.sfc"


def main():
    check_rom.check()
    rom = ROM.read_bytes()
    items, refs = scan(rom)
    out, writes = layout(rom, items, refs, texts(rom, items))
    errs, _ = romdiff.check(rom, out, set(), writes)
    if errs:
        sys.exit("\n".join(errs))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(out)
    (OUT.parent / "writes.txt").write_text(
        "".join(f"{o:06X} {a.hex()} {b.hex()} {n}\n" for o, a, b, n in writes if a != b), encoding="utf-8")
    same = "identical to the original" if out == rom else f"{sum(x != y for x, y in zip(rom, out))} bytes changed"
    print(f"{OUT.relative_to(ROOT)} sha1 {hashlib.sha1(out).hexdigest()} ({same})")


if __name__ == "__main__":
    main()
