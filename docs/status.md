# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1 (recon) done for text, pointers, compression and free space; the graphics survey covers the boot-route
  screens and waits on phase 2 for mid-game screens. Next: phase 2 (debug tool). Last build: none yet.
- **Done:**
  - Step 0: template, rulings D1-D8, ROM pin, MesenCE in `tools/mesen/`, guard hook, pre-commit check.
  - Phase 1: no earlier fan patch found (the series is *Hammerin' Harry* abroad; this SNES game stayed in Japan).
    Text is tiny: title speech bubble, staff credits, HUD labels, 5 stage names. Options and debug menus are already
    English. `docs/re/text.md`, `rom.md`, `graphics.md`; tables `tbl/jp.tbl`, `tbl/font.tbl`; RLE decompressor
    `tools/gfxcomp.py` (verified against VRAM) and `tools/gfx_blocks.py`; `tests/test_tables.py`.
  - Leftover debug stage/checkpoint select found: enter it by setting 7E:ED03 != 0 (or 7E:ECE9 = 1), C2:21E7.
- **Next:** Phase 2: a `tools/debug/` Lua warp that sets the debug flag and picks a menu row (scene list in
  `tools/debug/scenes.lua`: each stage half/checkpoint, each boss, FINAL), plus scenes the menu can't reach (stage
  clear, game over, continue, ending/credits: find their game-mode values). Shoot each, then finish the graphics
  survey (`docs/re/graphics.md` "Still to survey") and read font cells F7/FA/FB on the FINAL stage HUD.
- **Open bugs:** none.
- **Waiting on the user:** nothing. Defaults taken (non-blocking): the title logo gets redrawn in English as
  *Hammerin' Harry* (D5: an official English name exists); the ROM expands to 2 MiB for new text/font/graphics.
  Unchecked: Mesen GUI keyboard input (no interactive session).
