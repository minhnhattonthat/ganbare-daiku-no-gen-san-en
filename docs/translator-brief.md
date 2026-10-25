# Translator brief - Ganbare! Daiku no Gen-san (SNES, Irem 1993)

You translate part of the Japanese script of *Ganbare! Daiku no Gen-san* (the second *Hammerin' Harry* game) into
English for a fan patch. A comic action game for kids: Gen-san, a hot-headed Edo-style carpenter with a giant wooden
mallet, beats the crooked Kuromoku Gang until they reform. Work only on the batches named in your dispatch, one at a
time in the order given, each to a passing check before the next. Do all translation yourself; no subagents.

## Read first
1. `glossary.md` - rulings, style rules (voices), names and terms. Binding.
2. `docs/synopsis.md` - plot and who is who. Don't give the kidnapping away before chapter 3/4.
3. `build/terms_<batch>.txt` - the glossary rows that occur in this batch.

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`. Entries are in story order: use the neighbours for context.
- ` / ` separates the lines of one box. Translate the box as one utterance, then break it into lines yourself.
- `limit` = `<letters per line>x<lines per box>`; it is a HARD limit (the font is fixed-width: 1 letter, space or
  punctuation mark = 1 cell). `// ok` = the box may continue: ` // ` starts a new box of the same speaker
  (another panel/dialogue box). Use it rather than cutting meaning, but prefer one box when it fits.
  `UPPER` = uppercase-only font.
- Speakers marked `?` are guesses from the content; trust the Japanese if it says otherwise.
- `カ` in 源さんのカ / 何がカだ / わたしたちのカ is the kanji 力 "power, strength" (the font lacks 力).
- Credits: `role / name`, staff names in half-width katakana, Japanese order (family name first). Write
  `ROLE / GIVEN FAMILY` in Hepburn without macrons (ou/uu -> o/u: ｶﾄｳ ﾕｳｲﾁ -> YUICHI KATO). Drop the JP leading
  spaces (the build centres English credits). Use standard credit role names (GAME DESIGN, SOUND PROGRAMMING...).
- Stage names (b003): the HUD name after the `1-1 ` prefix (the build adds it back). Glossary forms are binding.
- Chapter cards: `<chapter label> <title>`. 序章 Prologue, 終章 Finale, N章前編/後編 = chapter N part 1/2; find a
  label form that fits 28 cells and use the same form on all ten cards.
- The epilogue ticker (`imm23285`) is one scrolling line; `{gap}` is a long pause in the scroll. Keep both `{gap}`
  codes in the same places (between the same sentences).

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII: straight quotes, `...`, `--`; no tabs inside
the English, no Japanese or fullwidth characters, no `[ ] { } \` (not in the font) except `{gap}`.
Line breaks: ` / ` (space slash space); new box: ` // `.

## Dry run and validate
- `python -X utf8 tools/fit.py "line one{nl}line two" --box panel` shows cells per line (boxes: page, panel, ending,
  card, continue, ticker, credit, stage).
- `python -X utf8 tools/batches.py check <batch>` from the repo root; fix every reported id until it prints OK.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese
  doesn't state; don't summarise or skip. Keep the punch of jokes and exclamations.
- Names and terms exactly as in the glossary (Gen-san, Kanna-chan, Genzo-kun, Kuromoku Gang, the Boss, mallet).
- No abbreviations to fit (no "Ch.", "Pt.", "&" for "and" in prose). If a line can't fit without losing meaning, use
  ` // ` where allowed, else keep the meaning and report `LONG: id`.
- Honorifics kept, Western order. Punctuation: ‼ -> `!!`, …… -> `...`, 「」 -> "...".
- Voices: see the glossary's Style rules. Gen-san is cocky and rough ("Teyandei!" stays as his catchphrase where the
  JP has てやんでい; a short gloss in the same line is fine if it fits, e.g. "Teyandei! Like heck!").
- A box's lines should break at natural phrase boundaries; no one-word stub as the last line if avoidable.

## Consistency
Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
