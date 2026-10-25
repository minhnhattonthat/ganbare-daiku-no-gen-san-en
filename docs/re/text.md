# Text

Addresses: HiROM, file offset = CPU address & 0x3FFFFF. Dump per `rom.sha1`.

## Font (verified)

- One 8x8 2bpp BG3 font, 256 tiles, raw at file **0x40000** (DMA'd from C4:0000 to VRAM $5400 by C2:0C5C). On the
  title and HUD screens tile = `$280 + code`. Code map: `tbl/font.tbl` (read off the font, cross-checked with the byte
  map below by `tests/test_tables.py`).
- Layout: `10-19` digits, `1A-33` A-Z, `34-3F` punctuation (`3F` = ©), `40-6F` hiragana あ..ぃ in gojuon order,
  `70-7F` small kana, ー, 、。「」 and the dakuten/handakuten marks, `80-B7` the same rows in katakana (code + $40),
  `C0-EF` box borders and pictures, `F0-FB` vertical-text dakuten and some pre-composed voiced kana (で べ が だ ジ).
- No voiced kana in the main rows: a voiced kana is the plain kana plus a mark tile (`7E`/`7F`) drawn in the row above.
  English needs no marks; the whole 0x40-0xBF block is free for a Latin VWF or a lowercase set.

## Format A: string renderer C0:9411 (verified)

- Called as `LDX #param; JSL $C09411` with a 6-byte param block: `x, y, attr, ptr24`. Params live in the WRAM copy of
  file 0x1000.. at 7E:9000.. (see `rom.md`), e.g. 7E:90DC..90EE = title screen.
- Each byte goes through the 256-byte map at **file 0x28200** (C2:8200) to a font code: **ASCII + JIS X 0201
  half-width kana** (`tbl/jp.tbl`). Writes tilemap words to the WRAM BG3 map at 7E:84C9 (DMA'd to VRAM $5C00).
- Half-width kana draw as hiragana; `\` or `~` (map value F9) toggles katakana (+$40). a-z also land on hiragana cells.
- Control bytes (after the map): `<` and `/` = FF end; `>` = FE next row; `$hh` = FD move cursor by two hex-digit
  args (row/col); `[` `]` `#` = FC/FB/FA toggle h/v/hv flip (box borders); `ﾞ` `ﾟ` = mark one row up-left of the
  previous glyph; `` ` `` = F0 vertical-text mark. Map values 0x7E-0xBF draw at `$20 - $42`.
- The renderer only does fixed 8x8 cells: English at 1 tile per letter, or a VWF later (phase 5).

### Known format-A text (all of it found so far)

| File | What | Pointer |
|---|---|---|
| 0x2B4EC | title speech-bubble frame (ASCII art) | param 7E:90DC (file 0x10DC) |
| 0x2B565 | title speech bubble, **vertical**: stored row by row across the columns, read right to left | param 7E:90E2 |
| 0x2B5A8.. | `© 1993 IREM CORP.`, `TM`, small marks | params 7E:90E8, 7E:90EE, 7E:90F4 |
| 0x2B890-0x2BA5B | staff credits, 17 strings, katakana roles and names | table at 0x2B846: `ptr16 (bank C2), 2 bytes` x17, FFFF end |
| 0x1113-0x11C8 | options menu (ATTACK/JUMP/SPECIAL/SOUND/BGM/EFFECT/LEVEL/EXIT): **already English** | 7E:9xxx |
| 0x1236-0x1440 | leftover debug stage select, `STAGE n (1ST HALF) CHKn` ... `FINAL STAGE`: English, debug only | table 7E:91DE, param 7E:91D8 |

Scanner (`work/re/scan_text.py`, throwaway) found no other format-A Japanese in the ROM: the game has very little text.

## Format B: raw font codes (verified)

- Stage names for the HUD, file **0x1070-0x10E7** (in the 7E:9000 copy), records `col, $39, row, 00, codes.., FF`;
  pointer table at file 0x105A (16-bit, 7E:90xx). Eight area records (1-1 .. 4-2, the name repeated per half) plus
  `FINAL` + name. Names: てやんで町, べらんめ森林, がってん谷, くろもくアジト (Edo-slang puns) and the final stage.

## Format C: tilemap words (verified)

- HUD layout block around file **0x2B400-0x2B4EB**: BG3 tilemap words, low byte = font code (labels とくてん,
  たいりょく, エリア, life/score digits). Loader not traced yet (guess: copied whole to the WRAM BG3 map).

## Not found yet

Stage intro cards, boss or ending text, game over / continue: none showed up in the scans. Check each when the debug
tool warps there (phase 2); if they are pictures they go in `graphics.md`.
