# ROM layout, free space, debug flags

## Header (verified)

- HiROM, 1 MiB (`$FFD7` = $0A), no SRAM, internal name `HAMMERIN' HARRY (JPN)`, map mode $31 (HiROM + FastROM).
- File offset = CPU address & 0x3FFFFF (banks C0-CF, mirrors 00-0F / 80-8F at $8000-$FFFF).

## Free space (verified as "none found")

- No 0x00/0xFF run at any of the 16 bank ends (each bank ends in live data). Treat the ROM as full.
- Plan: expand to 2 MiB (`$FFD7` = $0B, file 0x100000-0x1FFFFF = banks D0-DF, filled 0xFF) for new text, a VWF font
  and redrawn graphics. Checksum only in the release step. Verify the expanded banks are reachable with a boot test
  before code depends on them (phase 3/5).

## WRAM copy of file 0x1000.. (verified)

- File 0x1000.. is copied to **7E:9000..** at boot: the text param blocks (7E:90DC..), the stage-name records
  (file 0x1070) and their pointer table (file 0x105A), the options strings (0x1113..) and the debug-menu strings
  (0x1236..) are all addressed as 7E:9xxx. Moving any of it means repointing 16-bit 7E:9xxx pointers. Copy size: not
  measured yet.

## Compression (verified): `tools/gfxcomp.py`

- One decompressor, C2:01EA, `X/Y` = source lo/bank, destination WRAM (usually 7E:2000 tiles, 7E:0000 / 7E:7800 /
  7E:E000 maps). Block = type byte, word length, data stream, counts stream. Types 0-12 are byte/word RLE variants
  (described in the script), 14/16 raw words, 18/20 not decompression.
- `tools/gfx_blocks.py ROM` lists the 38 blocks named as `LDX #lo / LDY #bank` in code (10 tile sets + maps). Each
  decompresses cleanly; type 2 at 0x8ED54 matches the emulator's VRAM byte-for-byte (`tests/test_tables.py`).
- Logged loads on the boot route (`tools/lua/decomp_log.lua`): irem logo 0x7627E (+0x76645, 0x76788, 0x767B9),
  title 0x8ED54 (+0x919BC, 0x91E9F, 0x91EE2), menu book 0x8AF06 (+0x8DEBE, 0x8E98B, 0x8E9F6), intro house 0x91F41
  (+0x9648F, 0x96E7C, 0x96EED). Stage 1 graphics load without this decompressor (raw DMA).
- No recompressor yet: write one (and test `decompress(compress(x)) == x` on every block) when a graphic gets redrawn.

## Debug flags (verified in code, not yet run)

- C2:21E7: if 7E:ECE9 == 1, or 7E:ED03 != 0, the game enters a leftover **stage/checkpoint select** (C2:2200) instead
  of the normal flow. Its menu lists STAGE 1-4 halves with checkpoints CHK0-2, bosses and FINAL STAGE (strings at
  file 0x1236, table 7E:91DE). Phase 2's warp tool should set these flags from Lua.
