"""engine.py: the ROM size, code and font changes the English text needs (phase 5). build.py applies them after the
text layout; each patch names the original bytes it replaces, so romdiff rejects it on a wrong dump.

- **2 MiB:** header size byte $FFD7 0A -> 0B; file 0x100000-0x1FFFFF (banks D0-DF) starts as 0xFF. D0:0000-3FFF holds
  new code (CODE), the text blocks move to text_map.SLOT-sized slots from D0:4000 (MOVES).
- **Half-width story text (format D):** both glyph renderers (C2:0EBF, C0:95B1) draw only the left tile column of a
  glyph (tile 4N top, 4N+2 bottom) and step x by one cell; both typewriters (C2:0F63, C0:962A) step x by one cell.
  English glyphs (fonts/unifont_ascii.hex, colour 1) go into those two tiles of codes 00-5E (tbl/story_en.tbl).
- **Stage names (format B):** C2:130D read them from the 7E:9000 WRAM copy of file 0x1000.., which has no room.
  The hook reads the same pointer table from ROM (C0:1056) and the strings from their moved block.

    python -X utf8 tools/engine.py      # disassemble the hooks in build/gensan_en.sfc (needs the skill)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "fonts" / "unifont_ascii.hex"
SIZE = 0x200000
CODE = 0x100000  # D0:0000
STAGES = 0x1070  # text_map block of the stage names

# block lo -> slot; every text block moves, so the old ranges are free and every build exercises the moves
MOVES = {lo: 0x104000 + 0x4000 * k for k, lo in enumerate(
    (0x1070, 0x23CEC, 0x2B4EC, 0x2B643, 0x2B846, 0x2D836, 0x34ACB))}

NOP = 0xEA
# (file offset, original bytes, new bytes, why)
PATCHES = [
    (0xFFD7, b"\x0a", b"\x0b", "header: ROM size 2 MiB"),
    # C2:0F15 STA TL / INC / STA TR / INC / STA BL / INC / STA BR / INY / INX x4: drop the TR and BR stores (INC A
    # stays, so BL still gets tile 4N+2) and two INX (x += 1 cell)
    (0x20F1A, bytes.fromhex("9f02207e"), bytes([NOP] * 4), "C2:0F1A no TR tile (half-width)"),
    (0x20F24, bytes.fromhex("9f42207ec8e8e8e8e8"), bytes([NOP] * 4) + bytes.fromhex("c8e8e8") + bytes([NOP] * 2),
     "C2:0F24 no BR tile, x += 1 cell"),
    (0x95F9, bytes.fromhex("9fcb847e"), bytes([NOP] * 4), "C0:95F9 no TR tile (half-width)"),
    (0x9603, bytes.fromhex("9f0b857ec8e8e8e8e8"), bytes([NOP] * 4) + bytes.fromhex("c8e8e8") + bytes([NOP] * 2),
     "C0:9603 no BR tile, x += 1 cell"),
    (0x20FE6, bytes.fromhex("e620"), bytes([NOP] * 2), "C2:0FE6 typewriter x += 1 cell"),
    (0x96AB, bytes.fromhex("e620"), bytes([NOP] * 2), "C0:96AB typewriter x += 1 cell"),
    # C2:329E CPY #$004B: the epilogue ticker sets 7E:9026 bit 0 once its string index passes 0x4B (72 glyphs, 1152
    # frames at 16 per glyph). English letters type at 8 frames: the same moment is index 3 + 144
    (0x2329F, bytes.fromhex("4b00"), bytes.fromhex("9300"), "C2:329E ticker cue at the original time"),
    # C2:130D LDY $9056,x / LDX #$0698 -> JML D0:0000
    (0x2130D, bytes.fromhex("bc5690a29806"), bytes([0x5C, CODE & 0xFF, CODE >> 8 & 0xFF, 0xC0 | CODE >> 16, NOP, NOP]),
     "C2:130D stage name from ROM (JML stage_name)"),
    # HUD labels (format C, BG3 map words at 0x2B400, word 25 of a row = col 8): とくてん -> SCORE, たいりょく -> LIFE
    # (tile D8 = く + the bar's left cap, redrawn as the cap alone), エリア dropped: the stage name starts at col 8
    (0x2B432, bytes.fromhex("5300470052006d000000"), bytes.fromhex("2c001c0028002b001e00"), "HUD label SCORE"),
    (0x2B472, bytes.fromhex("4f00410067007500"), bytes.fromhex("250022001f001e00"), "HUD label LIFE"),
    (0x2B4B2, bytes.fromhex("8300a7008000"), bytes(6), "HUD label AREA dropped"),
    # title answer bubble params (x, y, ...): x 6 was the right column of the vertical kana; English lines start at 4
    (0x10EE, b"\x06", b"\x04", "title answer bubble x = 4 (as the first bubble)"),
    (0x40D80, bytes.fromhex("0804110c21184130215011280815000c"), bytes.fromhex("00000100010001000100010000010000"),
     "BG3 tile D8: bar cap without く"),
]


def stage_name(bank):
    """D0:0000, entered from C2:130D with A/X/Y 16-bit, X = (stage - 1) * 2, DB = 7E. Same loop as C2:1313, reading
    from bank `bank`; returns to C2:1329."""
    loop = bytes.fromhex("b90000" "29ff00" "c9ff00")    # LDA $0000,y / AND #$00FF / CMP #$00FF
    body = bytes.fromhex("090020" "9fc9847e" "e8e8c8")  # ORA #$2000 / STA $7E84C9,x / INX INX INY
    loop += bytes([0xF0, len(body) + 2]) + body          # BEQ done
    loop += bytes([0x80, 0x100 - len(loop) - 2])         # BRA loop
    return (bytes.fromhex("bf5610c0" "a8" "a29006" "8b")  # LDA $C01056,x / TAY / LDX #$0690 (col 8) / PHB
            + bytes([0xF4, bank, bank]) + b"\xab\xab"   # PEA bank:bank / PLB / PLB
            + loop
            + bytes.fromhex("ab" "5c2913c2"))            # done: PLB / JML $C21329


def glyphs():
    """{code: 16 rows} from the Unifont hex file, code = ASCII - 0x20."""
    out = {}
    for line in FONT.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            cp, hexrows = line.split(":")
            out[int(cp, 16) - 0x20] = bytes.fromhex(hexrows)
    return out


def font_patch(rom):
    """Font 0x41000: glyph N's top half into tile 4N, bottom half into tile 4N+2, 2bpp plane 0 (colour 1)."""
    lo, g = 0x41000, glyphs()
    hi = lo + 64 * (max(g) + 1)
    new = bytearray(rom[lo:hi])
    for n, rows in g.items():
        for half in (0, 1):
            t = 64 * n + 32 * half
            new[t:t + 16] = bytes(b for r in rows[8 * half:8 * half + 8] for b in (r, 0))
    return lo, bytes(rom[lo:hi]), bytes(new), "font: half-width English glyphs"


def expand(rom):
    return rom + b"\xff" * (SIZE - len(rom))


def apply(rom, writes=None):
    """Patch an expanded ROM (text already laid out) with the engine patches, or with `writes` when given.
    Returns (new rom, writes) for romdiff.py --writes."""
    out = bytearray(rom)
    if writes is None:
        code = stage_name(0xC0 | MOVES[STAGES] >> 16)
        writes = PATCHES + [font_patch(rom), (CODE, b"\xff" * len(code), code, "D0:0000 stage_name")]
    for off, old, new, why in writes:
        if rom[off:off + len(old)] != old:
            raise ValueError(f"{off:06X} {why}: expected {old.hex()}, ROM has {rom[off:off + len(old)].hex()}")
        out[off:off + len(new)] = new
    return bytes(out), writes


def main():
    import subprocess
    from skill import SKILL
    rom = ROOT / "build" / "gensan_en.sfc"
    dis = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "dis65816.py"), "--map", "hirom", str(rom)]
    for addr, n in (("C20F15", 14), ("C095F4", 14), ("C21309", 4), ("D00000", 22)):
        subprocess.run(dis + [addr, str(n)])


if __name__ == "__main__":
    main()
