# Engine changes (tools/engine.py, text_map moves)

All applied by `build.py`; each names the original bytes it replaces (romdiff checks them). `python -X utf8
tools/engine.py` disassembles the hooks in the current build.

| Where | Original | Change | Why |
|---|---|---|---|
| $FFD7 | `0A` (1 MiB) | `0B` (2 MiB) | banks D0-DF for code and moved text |
| C2:0F1A, C2:0F24 | glyph renderer stores TL TR BL BR, x += 4 bytes | stores TL (4N) and BL (4N+2) only, x += 2 bytes | half-width (8x16) story text, format D |
| C0:95F9, C0:9603 | same, twin renderer (cards, ending boxes) | same | same |
| C2:0FE6, C0:96AB | typewriter `INC $20` x2 per glyph | x1 | next letter one cell right |
| C2:130D | `LDY $9056,x / LDX #$0698` (stage name from the WRAM copy) | `JML D0:0000` | stage names read from ROM (moved block), no 7E:9000 size limit |
| D0:0000 | - | stage_name loop: table C0:1056, strings in the stage block's bank, `LDX #$0690` (col 8, was $0698 = col 12), back to C2:1329 | as above; 17 cells to the heart icon |
| 0x2B432, 0x2B472, 0x2B4B2 | HUD map words とくてん / たいりょ / エリア | SCORE / LIFE / blanks | format C labels in English, AREA dropped for the stage name |
| C2:14F9 | boss HUD row: `LDA #imm / STA $8B59..` て, blank, き (cols 8-10) + caps D9 (col 12), DA (col 23) | `JSL D0:0080 / BRA` to its `DEC $24 / RTS` | boss_label writes BOSS (4 cells) + the same caps |
| 0x40D80 | BG3 tile D8 = く + health bar's left cap | the cap alone | after LIFE |
| 0x41000 + 64N | 16x16 kana/kanji glyph N (TL, BL tiles) | Unifont ASCII glyph (code = ASCII - 0x20, N = 00-5E) | English story font; TR/BR tiles untouched, never drawn |

## Moved text blocks (text_map.layout `moves`, engine.MOVES)

Every text block moves to a 0x4000 slot from D0:4000 (never crossing a bank); the old range is padded with FF. Pointers
follow, including the second readers of a table's later fields:

- book page table: `LDA $C2D836,x` (+0, ptr) and `LDA $C2D838,x` (+2, bank) at C1:FA98/C1:FAA0;
- chapter script table: C1:FB51 (+0) and C1:FB57 (+2);
- credits table: C2:330D (+0), C2:331E (+2, x), C2:3325 (+3).

Bank bytes rewritten when the block moves (the strings' bank is set by code, not stored with the pointer):
`LDY #$00C2` at C2:3B62, C2:3E80, C2:3F1D (continue), C2:269D, C2:26FF (ending lists), C2:3287 (ticker),
`LDY #$00C3` at C2:2CA8 (cards), the credits param bank 7E:9502 (file 0x1502).

Long operands into a block that are *not* text pointers (checked by a sweep of every long-addressing opcode):
C2:49E9 `CMP $C2BA5C,x` (a table right after the credits block, never moved); the rest of the sweep hits were data.
