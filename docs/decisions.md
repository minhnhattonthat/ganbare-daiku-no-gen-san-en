# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-10-25 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). Owner's standing answer for one-shot runs. |
| D2 | 2026-10-25 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist (e.g. the US/EU *Hammerin' Harry* series), else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-10-25 | Credits | stay Japanese, translate | English. |
| D4 | 2026-10-25 | Abbreviations | engine work first (default), abbreviate | Skill default: full names and terms, engine work before shortening. |
| D5 | 2026-10-25 | Graphics text left in Japanese | none (default), list | Translate all of it (titles, menus, banners, cards); keep the Japanese logo only if it has no official English version. |
| D6 | 2026-10-25 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through checkpoints, report at the end. |
| D7 | 2026-10-25 | Existing saves / savestates | user's, none | None provided; build the debug tool as usual. |
| D8 | 2026-10-25 | Publishing | - | Never `gh release create`, never change repo visibility; the run ends at a built and verified release zip. Push to main at each phase end is approved. |
| D9 | 2026-10-26 | Publishing v1.0 | - | User: "continue to release and publish to github minhnhattonthat". Overrides D8 for v1.0: `gh release create v1.0` on minhnhattonthat/ganbare-daiku-no-gen-san-en approved. Visibility asked separately: user chose "Make public" (done 2026-10-26). |
| D10 | 2026-10-26 | Base dump (issue #1) and v1.1 | keep old dump, No-Intro | No-Intro (SHA-1 90b419d3); the old dump was a 4-byte hack (HDMA enable NOPed at C2:008D). User: "prepare release and publish", then "ok" to: re-run visual QA, `release.py --version 1.1`, push `fix/issue-1`, `gh release create v1.1` from it; no merge to main. |
