"""text_map.py: every string the game draws (formats A, B, D), the pointer structures that reach it, and the layout
that writes them back. build.py and the tests build on `scan()` and `layout()`; the reading code behind each table is
in docs/re/text.md.

    python -X utf8 tools/text_map.py [ROM]      # one line per string: id, name, header, text

A *block* is a file range that holds strings and their tables and nothing else; `layout()` re-packs each block in the
original order and rewrites every pointer, so with unchanged text it reproduces the ROM byte for byte (tests/).
Format C (HUD tilemap, fixed layout, no pointers) is not text here: it stays raw until phase 5 edits it as a map.
"""
import sys
from collections import namedtuple
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Ganbare! Daiku no Gen-san (Japan).sfc"
TABLES = {"A": "jp.tbl", "B": "font.tbl", "D": "story.tbl"}

# fmt None = a pointer table, kept as raw bytes apart from its pointer fields
Item = namedtuple("Item", "off end fmt head name")
# at = file offset of the pointer (code, or a field inside a table item); mode: long = 24-bit CPU address,
# short = 16-bit with the bank fixed by the reading code, wram = 16-bit into the 7E:9000 copy of file 0x1000..
Ref = namedtuple("Ref", "at mode target")

BLOCKS = [
    (0x1070, 0x10DC, "B stage names (in the 7E:9000 copy)"),
    (0x23CEC, 0x23D24, "D continue bubble"),
    (0x2B4EC, 0x2B643, "A title bubble, copyright, menu frame"),
    (0x2B643, 0x2B83C, "D ending boxes, epilogue ticker"),
    (0x2B846, 0x2BA5C, "A staff credits"),
    (0x2D836, 0x2E0A0, "D book pages, chapter scripts"),
    (0x34ACB, 0x34B88, "D chapter cards"),
]


def u16(rom, o):
    return rom[o] | rom[o + 1] << 8


def u24(rom, o):
    return (rom[o] | rom[o + 1] << 8 | rom[o + 2] << 16) & 0x3FFFFF


def scan(rom):
    """Walk every pointer structure. Returns (items by offset, refs); verified against the reading code (text.md)."""
    tables = {k: Table.load(ROOT / "tbl" / v) for k, v in TABLES.items()}
    items, refs = {}, []

    def string(off, fmt, hdr, name):
        if off not in items:
            _, used = tables[fmt].decode(rom, off + hdr)
            items[off] = Item(off, off + hdr + used, fmt, bytes(rom[off:off + hdr]), name)
        return off

    def table(off, end, name):
        items[off] = Item(off, end, None, b"", name)

    def ptr(at, mode, target):
        refs.append(Ref(at, mode, target))

    def list16(lst, stride, bank, fmt, hdr, name):  # ptr16 + (stride - 2) bytes per entry, FFFF end
        j = 0
        while u16(rom, lst + stride * j) != 0xFFFF:
            at = lst + stride * j
            ptr(at, "short", string(bank | u16(rom, at), fmt, hdr, f"{name}{j}"))
            j += 1
        table(lst, lst + stride * j + 2, f"{name}_list")

    # A: title params x,y,attr,ptr24 in the 7E:9000 copy (7E:90DC.., menu frame 7E:945E); credits read by C2:330D
    for p in (0x10DC, 0x10E2, 0x10E8, 0x10EE, 0x10F4, 0x145E):
        ptr(p + 3, "long", string(u24(rom, p + 3), "A", 0, f"title{p:04X}"))
    # every table address is read from the code that uses it, so a re-scan of a re-packed ROM follows the moves
    credits = u24(rom, 0x2330E)
    ptr(0x2330E, "long", credits)
    list16(credits, 4, 0x20000, "A", 0, "credit")
    # B: stage-name table at file 0x1056 (16-bit 7E:90xx), 13 entries (x-1, x-2, empty per area, FINAL);
    # the empty entries share FINAL's FF
    for i in range(13):
        at = 0x1056 + 2 * i
        ptr(at, "wram", string(u16(rom, at) - 0x8000, "B", 0, f"stage{i}"))
    # D: book pages C1:FA98, scripts C1:FB51, ending lists C2:269A/C2:26FC, cards C2:2AE6/C2:2CA3, immediates
    pages = u24(rom, 0x1FAA1)
    ptr(0x1FAA1, "long", pages)
    table(pages, pages + 15, "page_table")
    for i in range(5):
        ptr(pages + 3 * i, "long", string(u24(rom, pages + 3 * i), "D", 4, f"page{i}"))
    scripts = u24(rom, 0x1FB52)
    ptr(0x1FB52, "long", scripts)
    table(scripts, scripts + 30, "script_table")
    for i in range(10):
        s = u24(rom, scripts + 3 * i)
        ptr(scripts + 3 * i, "long", s)
        table(s, s + 1 + 11 * rom[s], f"script{i}")
        for j in range(rom[s]):
            at = s + 1 + 11 * j
            ptr(at, "long", string(u24(rom, at), "D", 4, f"script{i}.{j}"))
    for n, code in enumerate((0x2269B, 0x226FD)):  # LDX #lo / LDY #$00C2
        ptr(code, "short", 0x20000 | u16(rom, code))
        list16(0x20000 | u16(rom, code), 8, 0x20000, "D", 4, f"ending{n}.")
    cards = u24(rom, 0x22AE7)
    for code in (0x22AE7, 0x22CA4):
        ptr(code, "long", cards)
    table(cards, cards + 28, "card_table")
    for i in range(14):
        if u16(rom, cards + 2 * i):
            ptr(cards + 2 * i, "short", string(0x30000 | u16(rom, cards + 2 * i), "D", 4, f"card{i}"))
    for hdr, code in ((4, 0x23285), (3, 0x23B60), (4, 0x23E7E), (4, 0x23F1B)):  # LDX #lo / LDY #$00C2
        ptr(code, "short", string(0x20000 | u16(rom, code), "D", hdr, f"imm{code:05X}"))
    return items, refs


def sid(it):
    """Stable id of a string: format + original file offset."""
    return f"{it.fmt}{it.off:05X}"


def texts(rom, items):
    """{id: text} for every string as the ROM has it."""
    tables = {k: Table.load(ROOT / "tbl" / v) for k, v in TABLES.items()}
    return {sid(it): tables[it.fmt].decode(rom, it.off + len(it.head))[0] for it in items.values() if it.fmt}


def layout(rom, items, refs, text, pad=0xFF):
    """Re-pack every block from `text` ({id: text}) and rewrite all pointers. Returns (new rom, writes) where writes
    is [(offset, orig bytes, new bytes, name)] for romdiff.py --writes. Raises ValueError when a block overflows."""
    tables = {k: Table.load(ROOT / "tbl" / v) for k, v in TABLES.items()}
    out, new = bytearray(rom), {}
    for lo, hi, what in BLOCKS:
        pos, host = lo, None
        for it in sorted(i for i in items.values() if lo <= i.off < hi):
            data = it.head + tables[it.fmt].encode(text[sid(it)]) if it.fmt else rom[it.off:it.end]
            if host and it.off < host[0].end:  # the original shares the tail of the string before it
                if not host[1].endswith(data):
                    raise ValueError(f"{it.name}: shares {host[0].name}'s tail, which no longer ends in its bytes")
                new[it.off] = new[host[0].off] + len(host[1]) - len(data)
                continue
            new[it.off], host = pos, (it, data)
            pos += len(data)
            if pos > hi:
                raise ValueError(f"block {lo:05X} ({what}) overflows by {pos - hi} bytes at {it.name}")
            out[new[it.off]:pos] = data
        out[pos:hi] = bytes([pad]) * (hi - pos)

    # one logged write per block, plus one per pointer outside the blocks (code operands, the 7E:9000 tables)
    moved, writes = sorted(i for i in items.values() if not i.fmt), []
    for r in refs:
        at = next((new[t.off] + r.at - t.off for t in moved if t.off <= r.at < t.end), r.at)
        dest = new[r.target]
        if r.mode == "long":
            data = bytes([dest & 0xFF, dest >> 8 & 0xFF, rom[r.at + 2] & 0xC0 | dest >> 16])
        elif r.mode == "short":
            if dest >> 16 != r.target >> 16:
                raise ValueError(f"{r.target:05X} left its bank; the pointer at {r.at:05X} is 16-bit")
            data = (dest & 0xFFFF).to_bytes(2, "little")
        else:
            data = (dest + 0x8000).to_bytes(2, "little")
        out[at:at + len(data)] = data
        if not any(lo <= at < hi for lo, hi, _ in BLOCKS):
            writes.append((at, bytes(rom[at:at + len(data)]), data, f"ptr {r.at:05X}"))
    writes += [(lo, bytes(rom[lo:hi]), bytes(out[lo:hi]), what) for lo, hi, what in BLOCKS]
    return bytes(out), writes


def main():
    rom = Path(sys.argv[1] if len(sys.argv) > 1 else ROM).read_bytes()
    items, _ = scan(rom)
    t = texts(rom, items)
    for it in sorted(items.values()):
        if it.fmt:
            print(f"{sid(it)} {it.name:12} {it.head.hex()} {t[sid(it)]}")


if __name__ == "__main__":
    main()
