"""tools/gfx.py: the new tile and metatile blocks draw exactly the English images (no colour lost to the palette
pick, no tile id clash), and nothing outside the redrawn screens changes."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402
from gfxcomp import decompress  # noqa: E402
from text_map import ROM  # noqa: E402

needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="no ROM dump in rom/")


def redraw(tiles, defs, lay, gw, rect, colours):
    return gfx.render(tiles, defs, gfx.cells_of(lay, gw, rect), colours, (32 * rect[2], 32 * rect[3]))


@needs_rom
def test_title_blocks_draw_the_english_board():
    rom = ROM.read_bytes()
    imgs, blocks = gfx.title(rom)
    defs = struct.unpack("<880H", blocks[gfx.DEFS])
    lay = struct.unpack("<64H", decompress(rom, gfx.LAYOUT)[0])
    assert redraw(blocks[gfx.TILES], defs, lay, 8, gfx.BOARD, gfx.COLOURS).tobytes() == imgs[0][2].tobytes()
    # the forest layer (BG1, the other layout) keeps every tile it had
    old = decompress(rom, gfx.TILES)[0]
    old_defs = struct.unpack("<880H", decompress(rom, gfx.DEFS)[0])
    for m in struct.unpack("<56H", decompress(rom, 0x91E9F)[0]):
        for i in range(m // 2, m // 2 + 16):
            t = old_defs[i] & 0x3FF
            assert defs[i] == old_defs[i] and blocks[gfx.TILES][32 * t:32 * t + 32] == old[32 * t:32 * t + 32]


@needs_rom
def test_book_blocks_draw_the_english_plaques():
    rom = ROM.read_bytes()
    imgs, blocks = gfx.book(rom)
    n = len(blocks[gfx.B_DEFS]) // 2
    defs = struct.unpack(f"<{n}H", blocks[gfx.B_DEFS])
    lay = struct.unpack("<256H", decompress(rom, gfx.B_LAYOUT)[0])
    for (rect, _), (_, _, img) in zip(gfx.PLAQUES, imgs):
        assert redraw(blocks[gfx.B_TILES], defs, lay, 16, rect, gfx.B_PAL).tobytes() == img.tobytes()
    back = struct.unpack("<256H", decompress(rom, gfx.B_BACK)[0])
    got = redraw(blocks[gfx.B_TILES], defs, back, 16, gfx.BACK_RECT, gfx.B_PAL)
    assert got.tobytes() == imgs[-1][2].tobytes()


@needs_rom
def test_continue_blocks_draw_the_english_signs():
    rom = ROM.read_bytes()
    imgs, blocks = gfx.signs(rom)
    defs = struct.unpack(f"<{len(blocks[gfx.C_DEFS]) // 2}H", blocks[gfx.C_DEFS])
    lay = struct.unpack("<64H", decompress(rom, gfx.C_LAYOUT)[0])
    got = redraw(blocks[gfx.C_TILES], defs, lay, 8, (0, 0, 8, 8), gfx.C_PAL)
    assert got.tobytes() == imgs[0][2].tobytes()


@needs_rom
def test_shout_tiles_draw_teyandei_and_keep_the_bang():
    rom = bytearray(ROM.read_bytes())
    (orig, img), writes = gfx.shout(bytes(rom))
    assert writes and all(gfx.S_TILES <= off < gfx.S_TILES + 0x800 for off, *_ in writes)
    for off, _, new, _ in writes:
        rom[off:off + 32] = new
    (got, _), _ = gfx.shout(bytes(rom))
    assert got.tobytes() == img.tobytes()
    bang = (gfx.S_WORD, 0, 64, 32)
    assert img.crop(bang).tobytes() == orig.crop(bang).tobytes()
    assert img.crop((0, 0, gfx.S_WORD, 32)).getbbox()  # the word is drawn
