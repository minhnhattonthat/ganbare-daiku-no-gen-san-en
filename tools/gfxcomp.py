"""gfxcomp.py: the game's RLE decompressor (C2:01EB), for graphics and tilemaps.

Block = type byte, then word L (data-stream length), then L data bytes, then (types 0/2/6/8/12) a counts stream.
Flags are read MSB first; a set "count" flag takes the run length from the counts stream (0 = 256), else 1.
    type 0  byte runs        8 flags/byte: count?
    type 2  byte runs        4 elements/byte, 2 bits: count?, single? (single byte doubled / byte pair repeated)
    type 4  byte hold        8 flags/byte: new byte? (else repeat last; last resets to 0 at each flag byte)
    type 6  word runs        16 flags/word: count?
    type 8  word runs        8 elements/word, 2 bits: count?, single? (word doubled / word pair repeated)
    type 10 word hold        16 flags/word: new word?
    type 12 word ramp        16 flags/word: count? (word written count times, +1 each time)
    type 14, 16 raw words    L bytes copied
Types 18, 20 are not decompression (C2:0490 sets up something else).

    python tools/gfxcomp.py ROM OFFSET [OUT]     # decompress the block at a file offset
"""
import struct
import sys


def decompress(rom, off):
    """Return (data, packed_size) for the block at file offset off."""
    t = rom[off]
    L = struct.unpack_from('<H', rom, off + 1)[0]
    src = off + 3
    if t in (14, 16):
        return bytes(rom[src:src + L]), 3 + L
    cnt = src + L  # counts stream
    out = bytearray()
    y = 0

    def count():
        nonlocal cnt
        c = rom[cnt] or 256
        cnt += 1
        return c

    def b(i):
        return rom[src + i]

    def w(i):
        return rom[src + i:src + i + 2]

    if t == 0:
        while y < L:
            flags = b(y); y += 1
            for k in range(8):
                c = count() if flags & (0x80 >> k) else 1
                out += bytes([b(y)]) * c
                y += 1
                if y >= L:
                    break
    elif t == 2:
        while y < L:
            flags = b(y); y += 1
            for k in range(4):
                bits = (flags >> (6 - 2 * k)) & 3
                c = count() if bits & 2 else 1
                if bits & 1:
                    out += bytes([b(y)]) * (2 * c); y += 1
                else:
                    out += bytes([b(y), b(y + 1)]) * c; y += 2
                if y >= L:
                    break
    elif t == 4:
        while y < L:
            flags = b(y); y += 1
            last = 0
            for k in range(8):
                if flags & (0x80 >> k):
                    last = b(y); y += 1
                out.append(last)
    elif t in (6, 12):
        while y < L:
            flags = struct.unpack('<H', w(y))[0]; y += 2
            for k in range(16):
                c = count() if flags & (0x8000 >> k) else 1
                v = struct.unpack('<H', w(y))[0]
                for i in range(c):
                    out += struct.pack('<H', (v + (i if t == 12 else 0)) & 0xFFFF)
                y += 2
                if y >= L:
                    break
    elif t == 8:
        while y < L:
            flags = struct.unpack('<H', w(y))[0]; y += 2
            for k in range(8):
                bits = (flags >> (14 - 2 * k)) & 3
                c = count() if bits & 2 else 1
                if bits & 1:
                    out += bytes(w(y)) * (2 * c); y += 2
                else:
                    out += bytes(w(y) + w(y + 2)) * c; y += 4
                if y >= L:
                    break
    elif t == 10:
        while y < L:
            flags = struct.unpack('<H', w(y))[0]; y += 2
            last = b'\0\0'
            for k in range(16):
                if flags & (0x8000 >> k):
                    last = bytes(w(y)); y += 2
                out += last
    else:
        raise ValueError('type %d at %06x is not a compressed block' % (t, off))
    return bytes(out), cnt - off


if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    data, size = decompress(rom, int(sys.argv[2], 16))
    print('type %d packed %d -> %d bytes' % (rom[int(sys.argv[2], 16)], size, len(data)))
    if len(sys.argv) > 3:
        open(sys.argv[3], 'wb').write(data)
