# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1-4 done (extract 2026-10-25). Next: phase 5. Last build: `build/gensan_en.sfc` sha1
  7dc58aa0fcf643092e995897dae3de7bdfd05c6e = the original (identity from script/), smoke ok 2026-10-25.
- **Done:**
  - Step 0: template, rulings D1-D8, ROM pin, MesenCE in `tools/mesen/`, guard hook, pre-commit check.
  - Phase 1: no earlier fan patch (the series is *Hammerin' Harry* abroad). Known text: title bubble, staff credits,
    HUD labels, stage names; options/debug menus already English. `docs/re/text.md`, `rom.md`, `graphics.md`; tables
    `tbl/jp.tbl`, `tbl/font.tbl`; RLE decompressor `tools/gfxcomp.py`, `tools/gfx_blocks.py`; `tests/test_tables.py`.
  - Phase 2: `tools/debug/warp.lua` + `scenes.lua` drive the leftover stage select (7E:ED03) blind and can redirect
    the game's flow graph (`docs/re/flow.md`). 38 scenes: every stage half/checkpoint, bosses, FINAL, clear_1..13
    (story pages + map before each next stage; clear_13 = ending + staff roll), continue, game over.
    `python -X utf8 tools/debug/run_all.py` reaches all 38 from cold boot (38/38 on 2026-10-25), writes
    `work/qa/scenes/<name>.png` + `sheet.png` and `work/states/<name>.mss`. Options: `GOD=1`, `ADV=n` (press A
    every n frames: pages through story text and the ending).
  - Phase 1 gap: story script = format D (`docs/re/text.md`): 16x16 2bpp 160-glyph font at 0x41000, `tbl/story.tbl`,
    61 strings (book pages, dialogue panels, chapter cards, ending boxes, epilogue ticker, continue bubble) in four
    blocks, all reached through pointer tables/immediates. `tools/lua/textlog.lua` logs each string the renderers draw.
  - Phase 3: `tools/text_map.py` (replaces story_text.py) scans formats A, B, D from the code pointers (7 blocks,
    95 strings) and re-packs them; `build.py` = identity build, romdiff-checked write log. `tests/test_text_map.py`:
    roundtrip, block tiling, byte-identical rebuild, shortened strings move with all pointers. Found on the way: stage
    table starts at 0x1056 (13 entries, no record header), font cells F7/FA/FB = っ/ぞ/う, menu frame string 0x2B5C9.
    Format C (HUD tilemap) stays raw: fixed map, no pointers.
  - Phase 4: `tools/script.py dump` writes `script/<block>.json` (7 files, 95 strings; 4 title frame/mark strings
    and 2 empty ones are kind `data`, never translated). build.py writes `en` where filled, else `jp`.
    `tests/test_script.py`: every ROM string once with its current text, filled `en` encodes, blank script = original
    ROM, re-dump keeps `en`. The story font (D) has no Latin glyphs yet: `en` for D strings can't encode until phase 5.
- **Next:**
  1. Phase 5 decides the story font (8x16 half-width vs VWF in C2:0EBF/C0:95B1), expands to 2 MiB (boot-test the
     new banks), and gives blocks overflow room: ptr16 lists/immediates (`short` refs) keep their bank (C2/C3) unless
     the code's `LDY #$00C2`/bank operand is patched; stage names (block B) are boxed in by the title params.
     Marker build: every `text` entry -> `[id] marker`, boot each box, measure widths (width gate).
  2. Graphics recompressor (`decompress(compress(x)) == x` on all 38 blocks) when the first graphic is redrawn.
- **Open bugs:** none.
- **Gaps (non-blocking):** no warp for a won boss fight (the stage-clear moment inside stage play): fight AI with the
  cheat RAM didn't land hits; `go = {0x8053, 0}` skips straight to the clear handler instead. Boss intro/defeat
  sprites still to survey (`docs/re/graphics.md`). Map label/font cells F7/FA/FB not read yet.
- **Waiting on the user:** nothing. Defaults taken (non-blocking): the title logo gets redrawn in English as
  *Hammerin' Harry* (D5: an official English name exists); the ROM expands to 2 MiB for new text/font/graphics.
  Unchecked: Mesen GUI keyboard input (no interactive session).
