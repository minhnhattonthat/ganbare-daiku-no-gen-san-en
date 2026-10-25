# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2 (debug tool) done. Phase 1 reopened: the warps showed a kanji/kana story script the recon missed.
  Last build: none yet.
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
- **Next:**
  1. Phase 1 gap: find the story-script encoding, pointers and font (story pages, ending dialogue + epilogue ticker,
     continue bubble). Leads in `docs/re/text.md` "Not found yet". Update text ranges and free-space needs.
  2. Phase 3: identity build (`build.py`, byte-identical rebuild test).
- **Open bugs:** none.
- **Gaps (non-blocking):** no warp for a won boss fight (the stage-clear moment inside stage play): fight AI with the
  cheat RAM didn't land hits; `go = {0x8053, 0}` skips straight to the clear handler instead. Boss intro/defeat
  sprites still to survey (`docs/re/graphics.md`). Map label/font cells F7/FA/FB not read yet.
- **Waiting on the user:** nothing. Defaults taken (non-blocking): the title logo gets redrawn in English as
  *Hammerin' Harry* (D5: an official English name exists); the ROM expands to 2 MiB for new text/font/graphics.
  Unchecked: Mesen GUI keyboard input (no interactive session).
