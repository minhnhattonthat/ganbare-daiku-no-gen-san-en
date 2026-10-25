# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** Step 0 (repo setup) done. Next: phase 1 (research and recon). Last build: none yet.
- **Done:**
  - Template filled; rulings D1-D8 recorded (owner's one-shot answers).
  - ROM pinned: `rom.sha1` (No-Intro, 1 MiB, HiROM, internal name "HAMMERIN' HARRY (JPN)", no SRAM).
  - MesenCE 2.2.1 in `tools/mesen/`; original boots with `--smoke` via `tools/routes/boot.txt` (scripted Start changes screen; `tools/lua/probe_ok.lua` logs to log.txt). Settings in `tools/emu-config/mesen-settings.json`.
  - Guard hook (plugin) blocks the `sed -i` canary. Pre-commit `tools/hooks/pre-commit` (core.hooksPath) runs `tools/check.py`; a failing test was rejected.
  - `tools/tbl.py`, `bps.py`, `romdiff.py`, `skill.py` copied from the skill.
- **Next:** Phase 1: look for earlier patches/docs, find text encoding (relsearch on visible title/menu text), pointer tables, compression, control codes; graphics-text survey (title logo, red menu book, stage banners). Write `docs/re/*.md`. Get asar when phase 5 needs it.
- **Open bugs:** none.
- **Waiting on the user:** nothing. Unchecked: Mesen GUI keyboard input (no interactive session; Mesen writes default key mappings on first GUI start).
