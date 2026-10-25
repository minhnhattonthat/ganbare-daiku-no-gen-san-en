"""jp.tbl (text bytes) and font.tbl (glyph codes) must agree with the game's own byte->glyph map at file 0x28200,
and the RLE decompressor must reproduce a block the emulator decompressed (title BG tiles)."""
import hashlib
import sys
import unicodedata
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from gfxcomp import decompress  # noqa: E402
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Ganbare! Daiku no Gen-san (Japan).sfc"
needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="no ROM dump in rom/")


def kata_to_hira(c):
    return chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c


@needs_rom
def test_kana_bytes_match_font():
    rom = ROM.read_bytes()
    cmap = rom[0x28200:0x28300]
    jp, font = Table.load(ROOT / "tbl/jp.tbl"), Table.load(ROOT / "tbl/font.tbl")
    checked = 0
    for b in list(range(0xA6, 0xDE)) + list(range(0x30, 0x3A)) + list(range(0x41, 0x5B)):
        kata = unicodedata.normalize("NFKC", jp.dec[bytes([b])])
        code = cmap[b]
        assert font.dec[bytes([code])] == kata_to_hira(kata), hex(b)
        if b >= 0xA6 and b != 0xB0:  # {kana} adds $40: katakana cells (B7, katakana ー, left out of font.tbl)
            assert font.dec[bytes([code + 0x40])] == kata, hex(b)
        checked += 1
    assert checked == 56 + 10 + 26


@needs_rom
def test_decompress_title_tiles():
    rom = ROM.read_bytes()
    data, packed = decompress(rom, 0x8ED54)
    # sha1 of the 15136 bytes the game DMA'd from 7E:2000 to VRAM $1000 at f541 (Mesen VRAM dump, title screen)
    assert (len(data), packed) == (15136, 0x2C68)
    assert hashlib.sha1(data).hexdigest() == "d5bfe6d0f3bd3e0652607b97cb64cecbb3545a49"
