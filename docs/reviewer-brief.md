# Translation reviewer brief - Ganbare! Daiku no Gen-san

You review one batch of a JP->English fan translation. Read-only: no edits, no git, no subagents.
Mechanical validity (ids, encodable characters, width per line, glossary spellings) is already enforced by
`tools/batches.py check` - judge translation quality. Return the report as your final message: subagents cannot write
files, so the controller saves it.

## Inputs (paths in your dispatch)
- Pairs file `work/tl/<batch>.pairs.txt`: every entry as `>> id | speaker | JP` / `EN:` in story order. ` / ` =
  next line of the box, ` // ` = next box of the same speaker, `{gap}` = a pause in the scrolling ticker. Read ALL.
- `glossary.md` (rulings and voices at the top), `docs/synopsis.md`, the translator's report (unverified claims).
- Note: `カ` in 源さんのカ etc. is 力 "power" (font lacks the kanji). Speakers marked `?` are guesses.

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly (Gen-san, Kanna-chan, Genzo-kun, Kuromoku Gang, the Boss, mallet);
  honorifics kept; the chapter cards all use one label form; credits romanised in Hepburn, given name first.
- Things players caught that reviewers missed: jokes and exclamations losing their punch; abbreviated names or terms
  (none allowed); stock phrases that read awkwardly in English; one-word stub last lines.
- Naturalness and voice: Gen-san rough and cocky, Kanna-chan sweet, the Kansai thug brash, narrator cheering.

## Report
### Issues
#### Critical (meaning reversed, wrong speaker)
#### Important (clear mistranslation, glossary inconsistency, abbreviation)
#### Minor (style - these are deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN` (suggestions must fit the same line widths).
### Assessment
Approved | Needs fixes - one sentence why.
