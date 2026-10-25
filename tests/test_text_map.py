"""Text map (formats A, B, D): every string decodes with no unknown byte and re-encodes to the same bytes, strings plus
tables tile each block, and re-packing with unchanged text rebuilds the ROM byte for byte (the identity build)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tbl import Table  # noqa: E402
from text_map import BLOCKS, ROM, TABLES, layout, scan, sid, texts  # noqa: E402

needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="no ROM dump in rom/")


@pytest.fixture(scope="module")
def rom():
    return ROM.read_bytes()


@needs_rom
def test_strings_roundtrip(rom):
    items, _ = scan(rom)
    tables = {k: Table.load(ROOT / "tbl" / v) for k, v in TABLES.items()}
    for it in items.values():
        if it.fmt:
            text = texts(rom, {0: it})[sid(it)]
            # [F7]/[FB]: font.tbl duplicates of っ/う
            assert "[" not in text.replace("[F7]", "").replace("[FB]", ""), f"{it.name} unknown byte: {text}"
            assert it.head + tables[it.fmt].encode(text) == rom[it.off:it.end], it.name
    assert sum(it.fmt == "D" for it in items.values()) == 61


@needs_rom
def test_items_tile_blocks(rom):
    items, refs = scan(rom)
    for lo, hi, what, _ in BLOCKS:
        pos = lo
        for it in sorted(i for i in items.values() if lo <= i.off < hi):
            if it.off < pos:  # tail shared with the string before
                assert it.end == pos, f"{it.name} overlaps"
                continue
            assert it.off == pos, f"{what}: gap at {pos:05X} (next {it.name} at {it.off:05X})"
            pos = it.end
        assert pos == hi, f"{what} ends at {pos:05X}, expected {hi:05X}"
    assert all(r.target in items for r in refs)


@needs_rom
def test_identity_build(rom):
    items, refs = scan(rom)
    out, writes = layout(rom, items, refs, texts(rom, items))
    assert out == rom
    assert all(o == n for _, o, n, _ in writes)


@needs_rom
def test_shorter_string_moves_the_rest(rom):
    """Drop a glyph from the first string in each block: everything after it moves and every pointer follows."""
    items, refs = scan(rom)
    text = texts(rom, items)
    want = dict(text)
    for lo, hi, _, _ in BLOCKS:
        first = min(i for i in items.values() if lo <= i.off < hi and i.fmt and len(text[sid(i)]) > 6
                    and text[sid(i)][0] not in "{[")
        want[sid(first)] = text[sid(first)][1:]
    out, _ = layout(rom, items, refs, want)
    items2, _ = scan(out)
    got = {it.name: t for it in items2.values() if it.fmt for t in [texts(out, {0: it})[sid(it)]]}
    assert got == {it.name: want[sid(it)] for it in items.values() if it.fmt}
