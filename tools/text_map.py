"""text_map.py: every string the game draws (formats A, B, D), the pointer structures that reach it, and the layout
that writes them back. build.py and the tests build on `scan()` and `layout()`; the reading code behind each table is
in docs/re/text.md.

    python -X utf8 tools/text_map.py [ROM]      # one line per string: id, name, header, text

A *block* is a file range that holds strings and their tables and nothing else; `layout()` re-packs each block in the
original order and rewrites every pointer, so with unchanged text it reproduces the ROM byte for byte (tests/).
Format C (HUD tilemap, fixed layout, no pointers) is not text here: it stays raw until phase 5 edits it as a map.
"""
import re
import sys
from collections import namedtuple
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Ganbare! Daiku no Gen-san (Japan).sfc"
TABLES = {"A": "jp.tbl", "B": "font.tbl", "D": "story.tbl"}
EN_TABLES = TABLES | {"D": "story_en.tbl"}  # English D text is drawn with the half-width font (tools/engine.py)

# fmt None = a pointer table, kept as raw bytes apart from its pointer fields
Item = namedtuple("Item", "off end fmt head name")
# at = file offset of the pointer (code, or a field inside a table item); mode: long = 24-bit CPU address,
# short = 16-bit with the bank fixed by the reading code, wram = 16-bit into the 7E:9000 copy of file 0x1000..;
# add = the pointer holds target + add (code that reads fields of a table item)
Ref = namedtuple("Ref", "at mode target add", defaults=(0,))

# lo, hi, what, banks = file offsets of the bytes that hold the bank of the block's short pointers (LDY #$00C2
# operands, the credits' param bank at 7E:9502); `layout(moves=)` rewrites them when the block moves. Stage names
# (wram refs) can only move with the reader hook in tools/engine.py, which then supplies their bank.
BLOCKS = [
    (0x1070, 0x10DC, "B stage names (in the 7E:9000 copy)", ()),
    (0x23CEC, 0x23D24, "D continue bubble", (0x23B63, 0x23E81, 0x23F1E)),
    (0x2B4EC, 0x2B643, "A title bubble, copyright, menu frame", ()),
    (0x2B643, 0x2B83C, "D ending boxes, epilogue ticker", (0x2269E, 0x22700, 0x23288)),
    (0x2B846, 0x2BA5C, "A staff credits", (0x1502,)),
    (0x2D836, 0x2E0A0, "D book pages, chapter scripts", ()),
    (0x34ACB, 0x34B88, "D chapter cards", (0x22CA9,)),
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
    refs += [Ref(0x2331F, "long", credits, 2), Ref(0x23326, "long", credits, 3)]  # LDA $C2B848,x / $C2B849,x
    list16(credits, 4, 0x20000, "A", 0, "credit")
    # B: stage-name table at file 0x1056 (16-bit 7E:90xx), 13 entries (x-1, x-2, empty per area, FINAL);
    # the empty entries share FINAL's FF
    for i in range(13):
        at = 0x1056 + 2 * i
        ptr(at, "wram", string(u16(rom, at) - 0x8000, "B", 0, f"stage{i}"))
    # D: book pages C1:FA98, scripts C1:FB51, ending lists C2:269A/C2:26FC, cards C2:2AE6/C2:2CA3, immediates
    # both ptr24 tables are read in two parts: LDA $C2D838,x / LDA $C2D961,x fetch the bank byte (+2)
    pages = u24(rom, 0x1FAA1)
    ptr(0x1FAA1, "long", pages)
    refs.append(Ref(0x1FA99, "long", pages, 2))
    table(pages, pages + 15, "page_table")
    for i in range(5):
        ptr(pages + 3 * i, "long", string(u24(rom, pages + 3 * i), "D", 4, f"page{i}"))
    scripts = u24(rom, 0x1FB52)
    ptr(0x1FB52, "long", scripts)
    refs.append(Ref(0x1FB58, "long", scripts, 2))
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


SLOT = 0x4000  # a moved block gets a slot of this size: slots at multiples of it never cross a bank
PAGE = "{page}"  # in English panel/ending text: continue in a new panel/box (an extra entry, same layout bytes)
TOKEN = re.compile(r"\{[^}]*\}|\[[0-9A-Fa-f]{2}\]")
SCREEN = 32  # cells across the BG3 screen of the cards and credits (centred when English)


def entry_table(t):
    """(header bytes, entry stride, tail bytes) of a table with one string pointer per entry, else None: the script
    tables (count byte, ptr24 + 8 layout bytes) and the ending lists (ptr16 + 6 bytes, FFFF end), which their players
    walk entry by entry, so an entry can be repeated with another string ({page})."""
    if re.fullmatch(r"script\d+", t.name):
        return 1, 11, 0
    if re.fullmatch(r"ending\d\._list", t.name):
        return 0, 8, 2
    return None


def width(text):
    return max(len(TOKEN.sub("", s)) for s in re.split(r"\{nl\}|\{br\}", text))


def layout(rom, items, refs, text, en=(), moves=None, pad=0xFF):
    """Re-pack every block from `text` ({id: text}) and rewrite all pointers. Returns (new rom, writes) where writes
    is [(offset, orig bytes, new bytes, name)] for romdiff.py --writes. Raises ValueError when a block overflows.
    `en`: ids whose text is English (encoded with EN_TABLES). English D headers get half the typewriter delay (each
    half-width letter is half a glyph); English chapter cards type at 1 frame per letter (the card fades on a fixed
    timer) and are centred, like English credits (x byte of their table entry). {page} splits an English panel or
    ending box into several entries. `moves` {block lo: file offset}: the block goes to that SLOT (in the expanded
    ROM), its old range is padded, its bank bytes and short pointers follow."""
    tables = {k: Table.load(ROOT / "tbl" / v) for k, v in TABLES.items()}
    en_tables = {k: Table.load(ROOT / "tbl" / v) for k, v in EN_TABLES.items()}
    moves = moves or {}
    out, new, writes = bytearray(rom), {}, []

    # {page}: string off -> its parts; entry tables get one copy of the entry per extra part
    parts = {it.off: text[sid(it)].removesuffix("{end}").split(PAGE) for it in items.values()
             if it.fmt and sid(it) in en and PAGE in text[sid(it)]}
    by_at = {r.at: r for r in refs}
    remap, extra_refs, entry_of = {}, [], {}  # table off -> (old rel -> new rel); (ref, new abs, target key)
    for t in items.values():
        shape = not t.fmt and entry_table(t)
        if not shape:
            continue
        hdr, stride, tail = shape
        n = (t.end - t.off - hdr - tail) // stride
        targets = [by_at[t.off + hdr + stride * j].target for j in range(n)]
        for j, s in enumerate(targets):
            entry_of[s] = (t, j)
        extra = [len(parts.get(s, [0])) - 1 for s in targets]
        before = [sum(extra[:j]) for j in range(n)]
        remap[t.off] = lambda rel, hdr=hdr, stride=stride, n=n, before=before, total=sum(extra): (
            rel if rel < hdr else
            hdr + stride * (divmod(rel - hdr, stride)[0] + before[divmod(rel - hdr, stride)[0]])
            + (rel - hdr) % stride if rel < hdr + stride * n else rel + stride * total)
    for s in parts:
        if s not in entry_of:
            raise ValueError(f"{items[s].name}: {PAGE} only works in panel and ending-box text")

    def table_data(t):
        data = bytearray(rom[t.off:t.end])
        shape = entry_table(t)
        if shape:
            hdr, stride, tail = shape
            n = (t.end - t.off - hdr - tail) // stride
            body = bytearray(data[:hdr])
            for j in range(n):
                entry = data[hdr + stride * j:hdr + stride * (j + 1)]
                at = t.off + hdr + stride * j
                s = by_at[at].target
                body += entry
                for k in range(1, len(parts.get(s, [0]))):
                    extra_refs.append((by_at[at], len(body), t.off, (s, k)))
                    body += entry
            body += data[hdr + stride * n:]
            if hdr:
                if (len(body) - hdr) // stride > 255:
                    raise ValueError(f"{t.name}: more than 255 entries")
                body[0] = (len(body) - hdr) // stride
            data = body
        if t.name == "credit_list":  # ptr16, x, flag per entry, FFFF end: centre English credits
            for j in range(0, len(data) - 2, 4):
                s = 0x20000 | data[j] | data[j + 1] << 8
                if s in items and sid(items[s]) in en:
                    data[j + 2] = (SCREEN - width(text[sid(items[s])])) // 2
        return bytes(data)

    def string_data(it, body):
        if sid(it) not in en:
            return it.head + tables[it.fmt].encode(body)
        head = bytearray(it.head)
        if it.fmt == "D" and len(head) == 4:
            head[0] = max(1, head[0] // 2)
        if it.name.startswith("card"):
            head[0], head[1] = 1, (SCREEN - width(body)) // 2
        return bytes(head) + en_tables[it.fmt].encode(body)

    for lo, hi, what, banks in BLOCKS:
        start = moves.get(lo, lo)
        end = start + SLOT if lo in moves else hi
        pos, host = start, None
        for it in sorted(i for i in items.values() if lo <= i.off < hi):
            if not it.fmt:
                chunks = [(it.off, table_data(it))]
            elif it.off in parts:
                chunks = [(it.off if k == 0 else (it.off, k), string_data(it, p + "{end}"))
                          for k, p in enumerate(parts[it.off])]
            else:
                chunks = [(it.off, string_data(it, text[sid(it)]))]
            # the original shares the tail of the string before it: keep sharing while it still matches
            data = chunks[0][1]
            if len(chunks) == 1 and host and it.off < host[0].end and host[1].endswith(data):
                new[it.off] = new[host[0].off] + len(host[1]) - len(data)
                continue
            for key, data in chunks:
                new[key], host = pos, (it, data)
                pos += len(data)
                if pos > end:
                    raise ValueError(f"block {lo:05X} ({what}) overflows by {pos - end} bytes at {it.name}")
                out[new[key]:pos] = data
        out[pos:end] = bytes([pad]) * (end - pos)
        if lo in moves:
            out[lo:hi] = bytes([pad]) * (hi - lo)
            for b in banks:
                writes.append((b, rom[b:b + 1], bytes([0xC0 | start >> 16]), f"bank {what}"))
                out[b] = 0xC0 | start >> 16

    # one logged write per pointer outside the blocks (code operands, the 7E:9000 tables)
    tabs = sorted(i for i in items.values() if not i.fmt)
    jobs = [(r, next((new[t.off] + remap.get(t.off, lambda x: x)(r.at - t.off) for t in tabs
                      if t.off <= r.at < t.end), r.at), r.target) for r in refs]
    jobs += [(r, new[t] + rel, key) for r, rel, t, key in extra_refs]
    for r, at, key in jobs:
        dest = new[key] + r.add
        moved = any(lo <= r.target < hi and lo in moves for lo, hi, _, _ in BLOCKS)
        if r.mode == "long":
            data = bytes([dest & 0xFF, dest >> 8 & 0xFF, rom[r.at + 2] & 0xC0 | dest >> 16])
        elif r.mode == "short" or moved:  # a moved wram block is read from ROM by the engine's hook
            if dest >> 16 != r.target >> 16 and not moved:
                raise ValueError(f"{r.target:05X} left its bank; the pointer at {r.at:05X} is 16-bit")
            data = (dest & 0xFFFF).to_bytes(2, "little")
        else:
            data = (dest + 0x8000).to_bytes(2, "little")
        out[at:at + len(data)] = data
        inside = [(lo, hi) for lo, hi, _, _ in BLOCKS] + [(s, s + SLOT) for s in moves.values()]
        if not any(lo <= at < hi for lo, hi in inside):
            writes.append((at, bytes(rom[at:at + len(data)]), data, f"ptr {r.at:05X}"))
    for lo, hi, what, _ in BLOCKS:  # after the pointers: tables inside the blocks hold some of them
        writes.append((lo, bytes(rom[lo:hi]), bytes(out[lo:hi]), what))
        if lo in moves:
            s = moves[lo]
            writes.append((s, bytes(rom[s:s + SLOT]), bytes(out[s:s + SLOT]), what + " (moved)"))
    return bytes(out), sorted(writes)


def main():
    rom = Path(sys.argv[1] if len(sys.argv) > 1 else ROM).read_bytes()
    items, _ = scan(rom)
    t = texts(rom, items)
    for it in sorted(items.values()):
        if it.fmt:
            print(f"{sid(it)} {it.name:12} {it.head.hex()} {t[sid(it)]}")


if __name__ == "__main__":
    main()
