# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1 and 2 done (story-script gap closed 2026-10-25). Next: phase 3. Last build: none yet.
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
    blocks, all reached through pointer tables/immediates. `tools/story_text.py` walks them; `tests/test_story.py`
    roundtrips and checks block coverage. `tools/lua/textlog.lua` logs each string the renderers draw.
- **Next:**
  1. Phase 3: identity build (`build.py`, byte-identical rebuild test). Text formats to carry: A (`tbl/jp.tbl`),
     B (stage names), C (HUD tilemap), D (`tools/story_text.py`).
  2. Phase 4 extract into `script/`; phase 5 decides the story font (8x16 half-width vs VWF in C2:0EBF/C0:95B1).
- **Open bugs:** none.
- **Gaps (non-blocking):** no warp for a won boss fight (the stage-clear moment inside stage play): fight AI with the
  cheat RAM didn't land hits; `go = {0x8053, 0}` skips straight to the clear handler instead. Boss intro/defeat
  sprites still to survey (`docs/re/graphics.md`). Map label/font cells F7/FA/FB not read yet.
- **Waiting on the user:** nothing. Defaults taken (non-blocking): the title logo gets redrawn in English as
  *Hammerin' Harry* (D5: an official English name exists); the ROM expands to 2 MiB for new text/font/graphics.
  Unchecked: Mesen GUI keyboard input (no interactive session).
