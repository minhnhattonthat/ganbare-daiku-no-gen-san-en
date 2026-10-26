# Ganbare! Daiku no Gen-san English translation

Unofficial English fan translation of **Ganbare! Daiku no Gen-san** (Super Famicom, Irem, 1993; known abroad as the
*Hammerin' Harry* series): the source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/ganbare-daiku-no-gen-san-en
cd ganbare-daiku-no-gen-san-en
git config core.hooksPath tools/hooks                  # pre-commit runs tools/check.py
# copy your dump to: rom/Ganbare! Daiku no Gen-san (Japan).sfc
#   (1048576 bytes, no header, No-Intro SHA-1 90b419d3e71b17490f3aed0ad2ae3158af94ed33, CRC32 206BD866; the build refuses any other dump, see rom.sha1)
python -X utf8 build.py                                # -> build/gensan_en.sfc
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Irem's and is included only so
the translation can be checked against it. Ganbare! Daiku no Gen-san is (c) Irem; this project is not affiliated with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
