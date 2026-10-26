Ganbare! Daiku no Gen-san (SNES) - English Translation v{VERSION}
=================================================================

An unofficial fan translation of Irem's 1993 Super Famicom action game
"Ganbare! Daiku no Gen-san" (known abroad as the Hammerin' Harry series)
into English.

Translated:
- The whole story: the picture-book pages, dialogue panels, chapter cards,
  the ending, the epilogue ticker and the staff roll.
- The title screen logo (redrawn as HAMMERIN' HARRY), the book cover plaque,
  the back cover, the continue signs (YEAH! / NOPE) and the title bubble.
- The HUD (SCORE / LIFE / BOSS, English stage names), the boss's
  TEYANDEI! shout and the stage 1 arena poster.

The story uses a new half-width 8x16 font, and the ROM is expanded to 2 MiB to
make room for the English.

Applying the patch
------------------
Apply GanbareDaikuNoGenSan_EN_v{VERSION}.bps to an unmodified, unheadered dump
with Flips, Beat or RomPatcher.js (https://www.marcrobledo.com/RomPatcher.js/).

Base ROM: Ganbare! Daiku no Gen-san (Japan).sfc (No-Intro), 1,048,576 bytes
  {BASE}
Patched ROM: 2,097,152 bytes
  {PATCHED}

If your file is 1,049,088 bytes it has a 512-byte copier header: remove it first.

Notes
-----
- Tested in Mesen 2.2.1. Start from a fresh boot: save states made with the
  Japanese game carry the old text layout.
- Names: Gen-san, Kanna-chan, the Kuromoku Gang. Stage names keep the
  original's Edo-slang flavour (TEYANDE TOWN, BERANME WOODS...).

Known issues
------------
- None known. Please report anything you find.

Credits
-------
Translation, hacking and tools: minhnhattonthat, with AI assistance (Anthropic
Claude). Fonts: GNU Unifont and Lilita One (SIL Open Font License).

Bug reports: https://github.com/minhnhattonthat/ganbare-daiku-no-gen-san-en/issues

This is an unofficial fan work, not affiliated with Irem.
Do not distribute pre-patched ROMs.
