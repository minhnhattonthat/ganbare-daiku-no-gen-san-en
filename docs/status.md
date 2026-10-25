# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1-7 done (insert, fit, check 2026-10-26). Next: phase 8 (QA in the emulator). Last build:
  `build/gensan_en.sfc` sha1 6120fc2ca04187cb89061dcc216f81edf3e80779 (87 strings in English), smoke ok 2026-10-26.
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
    ROM, re-dump keeps `en`.
  - Phase 5: `tools/engine.py` (hooks in `docs/re/hooks.md`): 2 MiB, half-width 8x16 story font (Unifont ASCII,
    OFL, `fonts/`, `tbl/story_en.tbl`, code = ASCII - 0x20) by NOPing the TR/BR stores of both glyph renderers,
    stage names read from ROM by a hook at D0:0000, ticker cue C2:329E retimed. `text_map.layout` moves every block to
    a 0x4000 slot from D0:4000 (bank bytes + second-field readers of the page/script/credit tables follow), halves
    the typewriter delay for English, types cards at speed 1 and centres cards and credits, and `{page}` repeats a
    panel/ending entry (same speaker, new panel). `build.py --marker` = ruler markers + torture lines + a `{page}`
    demo; `tools/debug/tour.py` warps to the 16 text scenes and sheets them (16/16 ok on the marker build).
    Measured budgets in `data/windows.json` (page 27x4, panel 18x4 + {page}, ending 24x3 + {page}, continue 28,
    card 28, credit 28 uppercase, stage 13 incl. "1-1 ", ticker 330 letters); `tools/fit.py` lints them
    (`tests/test_fit.py`), `python -X utf8 tools/fit.py "text" --box panel` is the translators' dry run.
  - Phase 6: `glossary.md` (Gen-san / Genzo-kun, Kanna-chan, Kuromoku Gang (黒木組 read くろもく, per the stage name),
    the Boss), `docs/synopsis.md`, `data/speakers.json`, `docs/translator-brief.md`, `docs/reviewer-brief.md`.
    `tools/batches.py split|check|pairs|merge` (b001 story pages + panels, b002 cards/ending/ticker/continue, b003
    credits/stages; ` / ` = line, ` // ` = {page}, `{gap}` = ticker pause). One translator agent, one reviewer
    (approved, 0 Critical; the one Important and the Minors applied in the same pass). All 87 text entries merged into
    `script/` (`en`); `fit.py` clean. Translator TSVs in `work/tl/` (gitignored).
  - Phase 7: HUD stage name starts at col 8 (hook `LDX #$0690`, AREA label blanked, 17 cells): TEYANDE TOWN,
    BERANME WOODS, GATTEN VALLEY, KUROMOKU BASE. HUD labels SCORE / LIFE (tilemap words + tile D8 redrawn as the bar
    cap alone; `docs/re/hooks.md`); checked on 5 stage warps (`work/qa/hud/sheet.png`). New checks in
    `tools/check.py`: `tests/test_lint.py` (layout codes only, one {end}, credit {br} layout, no Japanese in `en`,
    untranslated only by `script/keep_jp.txt`, edge blanks, stub last lines, glossary EN + Avoid columns),
    `tests/test_engine.py` (vacated blocks all FF, no branch into a patched code span, stale-reader sweep of long
    operands and split LDX/LDY bank immediates; 12 triaged data hits listed). ROM-wide `jp_left.py --tbl` is pure
    noise here (codes reused by graphics/data, story codes reused by English); no slot list: every reachable string is
    rebuilt from script/ and the old ranges are FF (tested).
- **Next:**
  1. Phase 8: QA tour (`tools/debug/tour.py` + HUD warps) -> visual-QA subagents -> `qa_gate.py check` exit 0.
  2. Graphics text still Japanese (D5): title logo (redraw as *Hammerin' Harry*), title bubble (title10E2/10EE,
     vertical kana ASCII art, in `script/keep_jp.txt`: "If you need me, press START!" / "Let's go!"), menu book
     cover (G2), continue-screen signposts, boss intro/defeat sprites (survey). Each zoomed cold-boot shot English.
  3. Graphics recompressor (`decompress(compress(x)) == x` on all 38 blocks) when the first graphic is redrawn.
- **Open bugs:** none.
- **Gaps (non-blocking):** no warp for a won boss fight (the stage-clear moment inside stage play): fight AI with the
  cheat RAM didn't land hits; `go = {0x8053, 0}` skips straight to the clear handler instead. Boss intro/defeat
  sprites still to survey (`docs/re/graphics.md`). Map label/font cells F7/FA/FB not read yet. The continue screen's
  two signposts are Japanese graphics (graphics survey). Ticker cue C2:329E: what 7E:9026 bit 0 triggers is unread
  (only its timing is kept).
- **Waiting on the user:** nothing. Defaults taken (non-blocking): the title logo gets redrawn in English as
  *Hammerin' Harry* (D5: an official English name exists); the ROM expands to 2 MiB for new text/font/graphics;
  story font = fixed 8x16 half-width with `{page}` for long panels instead of a VWF (more panels, no abbreviation).
  Unchecked: Mesen GUI keyboard input (no interactive session).
