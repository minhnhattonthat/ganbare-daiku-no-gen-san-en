# Ganbare! Daiku no Gen-san (SNES) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md, `python tools/skill.py` prints it). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 build.py`        -> build/gensan_en.sfc (checks the dump against `rom.sha1` first) [not written yet: phase 3]
- Check:    `python -X utf8 tools/check.py`  (tests + lint; the pre-commit hook `tools/hooks/pre-commit` runs this; a fresh clone needs `git config core.hooksPath tools/hooks`)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/gensan_en.sfc --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 $SKILL/scripts/emu.py build/gensan_en.sfc --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 900 --sheet` (scenes: `tools/debug/scenes.lua`; never ask the user to play to a scene) [phase 2]
- Release:  `python -X utf8 tools/release.py` (patch + verify; never publish without the user) [phase 9]
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original ROM: `rom/Ganbare! Daiku no Gen-san (Japan).sfc` (1 MiB, no header; gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulator: this repo's own copy in `tools/mesen/` (MesenCE 2.2.1, https://github.com/nesdev-org/MesenCE/releases/download/2.2.1/Mesen_2.2.1_Windows.zip, via `fetch_emu.py mesen`; gitignored; settings in `tools/emu-config/`). Savestates: `work/states/`.
- Text: `script/` (format TBD in phase 4). Tables: `tbl/jp.tbl` (text bytes), `tbl/font.tbl` (BG3 glyph codes). Graphics RLE: `tools/gfxcomp.py`, block list `tools/gfx_blocks.py`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.
- Copied from the skill so the build runs without it: `tools/tbl.py`, `tools/bps.py`, `tools/romdiff.py`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Never run `gh release create`, never change repo visibility. The run ends at a built and verified release zip.
- Boot route `tools/routes/boot.txt`: the original reaches the house/stage intro at ~f1800; the frame right after the second Start is black (fade), so smoke needs the 900-frame tail.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
