"""gfx_blocks.py: list compressed blocks the code names as `LDX #lo / LDY #bank` (A2 lo hi A0 bb 00), the form
the loaders at C2:0B62.. take, and check each decompresses cleanly.

    python -X utf8 tools/gfx_blocks.py ROM [--out DIR]   # DIR: write each block decompressed as <off>.bin
"""
import argparse
import re
from pathlib import Path

from gfxcomp import decompress

TYPES = {0, 2, 4, 6, 8, 10, 12, 14, 16}


def find_blocks(rom):
    found = {}
    for m in re.finditer(rb'\xa2(..)\xa0(.)\x00', rom, re.S):
        lo, bank = int.from_bytes(m.group(1), 'little'), m.group(2)[0]
        if bank < 0xC0 or lo < 0x0000:
            continue
        off = ((bank & 0x3F) << 16) | lo
        if off + 3 > len(rom) or rom[off] not in TYPES:
            continue
        try:
            data, size = decompress(rom, off)
        except (IndexError, ValueError):
            continue
        if data and off not in found:
            found[off] = (m.start(), rom[off], size, len(data))
    return found


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('rom')
    ap.add_argument('--out')
    a = ap.parse_args()
    rom = open(a.rom, 'rb').read()
    blocks = find_blocks(rom)
    for off, (ref, t, size, n) in sorted(blocks.items()):
        print('%06x type=%-2d packed=%5d unpacked=%5d ref=%06x' % (off, t, size, n, ref))
        if a.out:
            Path(a.out).mkdir(parents=True, exist_ok=True)
            Path(a.out, '%06x.bin' % off).write_bytes(decompress(rom, off)[0])
    print(len(blocks), 'blocks')
