# Graphics text survey

Tile-drawn Japanese, one row each. Font-drawn text (formats A/B/C in `text.md`) is not listed here. Shots:
`work/qa/tour1`, `work/qa/boot`, `work/qa/book` (boot route); static renders: `work/re/sweep/` (`c_<off>.png` =
decompressed tile set, `raw_<bank>.png` = raw 4bpp bank).

| # | Screen | Element | Layer | Source | State |
|---|---|---|---|---|---|
| G1 | title | logo がんばれ! 大工の源さん on the wood board | BG2 | tiles 0x8ED54, 4x4 metatile defs 0x919BC, layout 0x91EE2 (8x8 metatiles; 0x91E9F = BG1 forest) | **English** (`tools/gfx.py` title: HAMMERIN' / HARRY), zoomed in game |
| G2 | menu book (after title) | cover plaque 大工の源さん (+ its copy on the lifting cover) | BG1 | tiles 0x8AF06, defs 0x8DEBE, layouts per variant in table C2:33D7 (BG1 0x8E98B, BG2 0x8E9F6; variant 1 = back cover 0x8EB23/0x8EC27) | **English** (`tools/gfx.py` book), both frames zoomed in game |
| G3 | back cover after the ending (clear_13 ~f16400) | ©アイレム line (+ English `PRESENTED BY irem`, a catalogue number), flat and on the closing cover | BG1 | 0x8AF06, layout 0x8EB23 (book variant 1; layout words carry flags in the low 5 bits) | **English** ©IREM (`tools/gfx.py` back_cover), both frames zoomed in game |
| G4 | in-stage HUD | small icons only; labels are font text (`text.md` format C) | BG3 | - | seen |
| G5 | irem logo, intro house (`NEW` letters) | English already | - | 0x7627E, 0x91F41 | seen, nothing to do |
| G6 | continue (warp `continue`) | two carved wooden signposts: retry やるぜ! (left) / quit けえるぞ (right) | BG1 | tiles 0x788C5, defs 0x792F5, layout 0x7949C (loader C2:3ACA) | **English** YEAH! / NOPE (`tools/gfx.py` signs), zoomed in game |
| G7 | in-stage hits | impact bursts (`BAM!`-style) | OBJ | raw banks CA-CF | seen small; read zoomed in phase 8 |

Not graphics (font text, belongs in `text.md`; phase-1 scan missed them): story-book pages before each stage
(warps `clear_2`..`clear_12`), the ending dialogue box (`ending`), the continue speech bubble, the ending epilogue
ticker that scrolls along the bottom of the night-city scene, the cast/staff roll, and the map's chapter label
(`n章前編/後編`, the known stage-name records).

## Still to survey

- Boss intros/defeats and the stage-clear moment inside stage play (needs a boss win: no warp yet, see
  `docs/status.md`), and 2-player screens if any.
- Static sweep with real palettes: render each tile set with the palette from its scene's PPU dump
  (`tools/gfx_blocks.py --out`, then `tiles.py render --pal`) and hand the sheets to read-only reviewers.
