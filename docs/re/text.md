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

Scanner (`work/re/scan_text.py`, throwaway) found no other format-A Japanese in the ROM. The story script is a
separate format (format D below).

## Format B: raw font codes (verified)

- Stage names for the HUD, file **0x1070-0x10E7** (in the 7E:9000 copy), records `col, $39, row, 00, codes.., FF`;
  pointer table at file 0x105A (16-bit, 7E:90xx). Eight area records (1-1 .. 4-2, the name repeated per half) plus
  `FINAL` + name. Names: てやんで町, べらんめ森林, がってん谷, くろもくアジト (Edo-slang puns) and the final stage.

## Format C: tilemap words (verified)

- HUD layout block around file **0x2B400-0x2B4EB**: BG3 tilemap words, low byte = font code (labels とくてん,
  たいりょく, エリア, life/score digits). Loader not traced yet (guess: copied whole to the WRAM BG3 map).

## Format D: story font (verified)

All story text: book pages, page dialogue panels, chapter cards, ending boxes and epilogue ticker, continue bubble.
Verified: `tools/lua/textlog.lua` logged every pointer the renderers got on warps clear_1..13, continue, gameover
(no other caller); `tests/test_story.py` decodes all 61 strings with no unknown byte, re-encodes them, and checks that
strings + tables tile each block below with no gap.

- **Font:** 160 glyphs, 16x16, 2bpp, 4 tiles per glyph (TL TR BL BR), raw at file **0x41000** (0x2800 bytes, DMA'd by
  C2:0CAC to VRAM $4000 = word $4000-$53FF, right below the BG3 8x8 font at $5400). Glyph code N = tiles 4N..4N+3
  (+ `attr` palette bits, + $2000 priority). Codes `00` space, `01-3F` hiragana/voiced kana, `3E-48` the katakana
  used, `49-4C` full-width 1-4, punctuation `4D-53`, `54-9D` 74 kanji, `9E` small ゃ; `9F` unused. Pre-composed
  voiced kana (no mark tiles). Table `tbl/story.tbl`.
- **String:** header, then 1 byte per glyph; `FE` = next line (y += 2 rows), `FD` = half line (y += 1), `FF` = end.
  Typewriter header (4 bytes): `speed` (frames per glyph), `x`, `y` (8x8 tile cells), `attr`. Instant form (C2:0EBF,
  only the continue bubble): 3 bytes `x`, `y`, `attr`. The x/y are absolute tile cells: each glyph is 2 cells wide.
- **Renderers:** typewriter C2:0F63 (per glyph C2:0EBF) and its twin C0:962A (per glyph C0:95B1, used by chapter
  cards and ending boxes); they write BG tilemap words into WRAM 7E:2000/2800, DMA'd to VRAM $7800/$7C00 every 4 frames.
- **Width (longest Japanese line):** book page 13 glyphs (208 px) x 4 lines, dialogue panel 9, ending box 12 x 3,
  chapter card 12, continue bubble 14; epilogue ticker one 164-glyph line. Real box widths: measure in phase 5.

| Block (file) | What | Pointers |
|---|---|---|
| 0x2D836 | page table: 5 x ptr24 | C1:FA98 `LDA $C2D836,x`, x = $50*3 |
| 0x2D845-0x2D95E | 5 book-page narrations (pages with a picture) | page table |
| 0x2D95F | script table: 10 x ptr24 (entries 0 and 1 the same) | C1:FB51 `LDA $C2D95F,x`, x = $30*3 |
| 0x2D97D-0x2E09F | 9 chapter scripts: `count`, count x (`ptr24` + 8 bytes: portrait/panel layout), then the strings (35 dialogue-panel lines) | script table |
| 0x2B643, 0x2B665 | ending box lists: (`ptr16` bank C2 + 6 bytes box/portrait), `FFFF` end | C2:269A `LDX #$B643`, C2:26FC `LDX #$B665` |
| 0x2B67F-0x2B792 | 7 ending dialogue boxes (3 lines, x=4) | ending lists |
| 0x2B793-0x2B83B | epilogue ticker, one line padded with `00` | C2:3284 `LDX #$B793` (`LDY #$00C2`) |
| 0x23CEC-0x23D23 | continue bubble (instant) and its two answers | C2:3B5F, C2:3E7D, C2:3F1A `LDX #imm` (`LDY #$00C2`) |
| 0x34ACB | chapter-card table: 14 x ptr16 (bank C3), by stage 7E:ECC7, 0 = no card | C2:2AE6, C2:2CA3 |
| 0x34AE7-0x34B87 | 10 chapter cards (prologue, 1-4 first/second half, finale) | card table |

Total 2,377 bytes of strings (headers included) in four blocks; no free space beside any of them (rom.md). Insertion plan
(phase 5): put English in the expanded banks; ptr24 tables repoint anywhere; the bank-fixed ptr16 lists and the
`LDX/LDY` immediates need their bank operand (`LDY #$00C2`, the card code's `LDY #$00C3`, the ending list bank) patched
or the strings kept in C2/C3. The 16x16 cell font gives 13 letters per line at 2 cells each: English needs an 8x16
half-width font (1 cell per letter, 26 per line) or a VWF in the renderer. Glyph slots: 160, VRAM fixed at $4000-$53FF.
