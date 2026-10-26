# Visual-QA reviewer brief - Ganbare! Daiku no Gen-san (SNES)

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- Optional: the original ROM's sheets (`work/qa/tour_jp/`, same ids) and `glossary.md`.

`$SKILL` = the path `python tools/skill.py` prints (run it from the repo root).

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out work/qa/scratch/<name>.png` and
  read that. Each sheet tile is one 256x224 frame (the sheet halves it unless `--div 1`): the frame PNGs themselves
  are in the same folder as the sheet (`f<frame>.png`), so for small text zoom the frame, not the sheet.
- When something looks wrong, open the same id from `tour_jp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.

## Judge
An `issue` is any of:
- Japanese still visible (kana or kanji anywhere: text boxes, signs, title, HUD, sprites);
- text overflowing a box, clipped by a frame, or running off screen;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok`:
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp;
- anything identical in the original's sheet.
- Every scene is a cold-boot warp: its first frames show the irem logo, the title screen and the red menu book.
  That is the route there, not a bug.
- The title board reads HAMMERIN' HARRY (the series' English name, docs/decisions.md D5) while the dialogue calls
  the hero Gen-san: intended. The title bubble says NEED A / HAND? / PRESS / START!, then LET'S / GO!.
- Story text (book pages, dialogue panels, ending boxes) uses a half-width 8x16 font with some letter spacing;
  long panels continue in a second panel of the same speaker.
- The epilogue ticker scrolls one long line along the bottom of the night-city scene; a sentence cut at either
  screen edge is the scroll.
- The yellow `STAGE n (1ST HALF) CHKn` line right after a warp is the leftover debug stage select (English in
  the original too), even when its number differs from the stage reached.
- Boss fights: a third HUD row BOSS with a green bar. Beating an enemy or losing a life pops up a flaming
  TEYANDEI! (Gen-san's catchphrase).
- Staff roll: cards scroll in from the right while the old one scrolls out left, as in the original. Its font's
  A has an open top (looks like a 4): the game's own Latin font.
- HUD: SCORE, LIFE and the English stage name (TEYANDE TOWN, BERANME WOODS, GATTEN VALLEY, KUROMOKU BASE).
- After the ending and back cover the game runs its attract demo (gameplay with no input): not a bug.
- The book cover lifting/closing animation shows the plaque or back cover skewed for a few frames.

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
