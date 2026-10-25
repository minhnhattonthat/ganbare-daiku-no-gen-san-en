# Graphics text survey

Tile-drawn Japanese, one row each. Font-drawn text (formats A/B/C in `text.md`) is not listed here. Shots:
`work/qa/tour1`, `work/qa/boot`, `work/qa/book` (boot route); static renders: `work/re/sweep/` (`c_<off>.png` =
decompressed tile set, `raw_<bank>.png` = raw 4bpp bank).

| # | Screen | Element | Layer | Source | State |
|---|---|---|---|---|---|
| G1 | title | logo がんばれ! 大工の源さん on the wood board | BG1/2 | compressed tiles 0x8ED54 + maps 0x919BC, 0x91E9F, 0x91EE2 | seen f1100 |
| G2 | menu book (after title) | cover label 大工の源さん | BG | compressed tiles 0x8AF06 + maps 0x8DEBE, 0x8E98B, 0x8E9F6 | seen f1000 |
| G3 | unknown (opening / book pages?) | slanted printed text in the same tile set as G2: a katakana ©-line with the year, `PRESENTED BY` (English), a catalogue number | BG | 0x8AF06 | static sweep only; find the screen in phase 2 |
| G4 | in-stage HUD | small icons only; labels are font text (`text.md` format C) | BG3 | - | seen |
| G5 | irem logo, intro house (`NEW` letters) | English already | - | 0x7627E, 0x91F41 | seen, nothing to do |

## Still to survey (needs the phase-2 warp tool)

- Every stage start (1-4, FINAL), each boss intro and defeat, stage clear, game over, continue, 2-player screens,
  ending and staff roll. Sprite text (e.g. GO / boss name tags) streams raw from banks CA-CF (`raw_c..f.png`); look at
  each in a zoomed in-game shot, the grey static renders are not readable enough for small sprite text.
- Static sweep with real palettes: render each tile set with the palette from its scene's PPU dump
  (`tools/gfx_blocks.py --out`, then `tiles.py render --pal`) and hand the sheets to read-only reviewers.
