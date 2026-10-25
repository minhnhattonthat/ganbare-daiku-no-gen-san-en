"""Format D (story font) text: walk every pointer structure and list the strings, with the bytes each structure owns.

    python -X utf8 tools/story_text.py [ROM]      # one line per string: offset, kind, header, text

Layout and the code that reads each table: docs/re/text.md "Format D". `strings(rom)` is what extract/insert build on.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Ganbare! Daiku no Gen-san (Japan).sfc"
TABLE = ROOT / "tbl" / "story.tbl"

# (kind, file offset of the pointer table / list, entries) - all verified against the reading code, see text.md
PAGES = (0x2D836, 5)       # ptr24 x5, read by C1:FA98 (index = $50)
SCRIPTS = (0x2D95F, 10)    # ptr24 x10 -> count, count x (ptr24 + 8 bytes), read by C1:FB51 (index = $30)
ENDING = (0x2B643, 0x2B665)  # ptr16 (bank C2) + 6 bytes, FFFF end; read via C2:269A / C2:26FC
CARDS = (0x34ACB, 14)      # ptr16 (bank C3) x14, 0 = no card; read by C2:2AE6 / C2:2CA3 (index = stage 7E:ECC7)
# (string offset, header length, file offset of the 16-bit pointer operand in code)
IMMEDIATE = [(0x2B793, 4, 0x23285), (0x23CEC, 3, 0x23B60), (0x23CFE, 4, 0x23E7E), (0x23D11, 4, 0x23F1B)]


def u16(rom, o):
    return rom[o] | rom[o + 1] << 8


def u24(rom, o):
    return (rom[o] | rom[o + 1] << 8 | rom[o + 2] << 16) & 0x3FFFFF


def strings(rom):
    """Yield (offset, header_len, kind) per string reference, in table order (a string shared by two refs repeats).
    Also yields ("table", start, end) spans for the pointer structures themselves, as (start, -1, end)."""
    for i in range(PAGES[1]):
        yield u24(rom, PAGES[0] + 3 * i), 4, f"page{i}"
    yield PAGES[0], -1, PAGES[0] + 3 * PAGES[1]
    yield SCRIPTS[0], -1, SCRIPTS[0] + 3 * SCRIPTS[1]
    for i in range(SCRIPTS[1]):
        s = u24(rom, SCRIPTS[0] + 3 * i)
        yield s, -1, s + 1 + 11 * rom[s]
        for j in range(rom[s]):
            yield u24(rom, s + 1 + 11 * j), 4, f"script{i}.{j}"
    for n, lst in enumerate(ENDING):
        j = 0
        while u16(rom, lst + 8 * j) != 0xFFFF:
            yield 0x20000 | u16(rom, lst + 8 * j), 4, f"ending{n}.{j}"
            j += 1
        yield lst, -1, lst + 8 * j + 2
    yield CARDS[0], -1, CARDS[0] + 2 * CARDS[1]
    for i in range(CARDS[1]):
        p = u16(rom, CARDS[0] + 2 * i)
        if p:
            yield 0x30000 | p, 4, f"card{i}"
    for off, hdr, _ in IMMEDIATE:
        yield off, hdr, f"imm{off:05X}"


def main():
    rom = Path(sys.argv[1] if len(sys.argv) > 1 else ROM).read_bytes()
    t = Table.load(TABLE)
    seen = set()
    for off, hdr, kind in strings(rom):
        if hdr < 0 or off in seen:
            continue
        seen.add(off)
        text, used = t.decode(rom, off + hdr)
        print(f"{off:06X} {kind:12} {rom[off:off + hdr].hex()} {text}")


if __name__ == "__main__":
    main()
