"""Format D (story text): every string reached through the pointer structures decodes with no unknown byte, re-encodes
to the same bytes, and the strings plus tables tile each text block with no gap or overlap (docs/re/text.md)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from story_text import ROM, TABLE, strings  # noqa: E402
from tbl import Table  # noqa: E402

needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="no ROM dump in rom/")
BLOCKS = [(0x23CEC, 0x23D24), (0x2B643, 0x2B83C), (0x2D836, 0x2E0A0), (0x34ACB, 0x34B88)]


@needs_rom
def test_story_strings_roundtrip_and_cover_blocks():
    rom = ROM.read_bytes()
    t = Table.load(TABLE)
    spans = {}
    for off, hdr, end_or_kind in strings(rom):
        if hdr < 0:
            spans[off] = end_or_kind
            continue
        text, used = t.decode(rom, off + hdr)
        assert "[" not in text, f"{off:06X} unknown byte: {text}"
        assert t.encode(text) == rom[off + hdr:off + hdr + used], f"{off:06X}"
        spans[off] = off + hdr + used
    assert len({o for o, h, _ in strings(rom) if h >= 0}) == 61
    for lo, hi in BLOCKS:
        pos = lo
        for s in sorted(o for o in spans if lo <= o < hi):
            assert s == pos, f"gap or overlap at {pos:06X} (next span {s:06X})"
            pos = spans[s]
        assert pos == hi, f"block {lo:06X} ends at {pos:06X}, expected {hi:06X}"
