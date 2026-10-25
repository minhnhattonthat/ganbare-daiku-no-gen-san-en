# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| fonts/unifont_ascii.hex | GNU Unifont 15.1.05, https://unifoundry.com/pub/unifont/unifont-15.1.05/font-builds/ | SIL OFL 1.1, or GPLv2+ with the GNU font embedding exception (https://unifoundry.com/LICENSE.txt) | yes (OFL: name the font and its licence in the README) | story text (format D), 8x16 half-width, written by tools/engine.py | ASCII 0x20-0x7E only, unaltered |
| fonts/LilitaOne-Regular.ttf (+ LilitaOne-OFL.txt) | Lilita One, Juan Montoreano, https://github.com/google/fonts/tree/main/ofl/lilitaone | SIL OFL 1.1 (Reserved Font Name "Lilita") | yes (name the font and its licence in the README) | title board lettering HAMMERIN' / HARRY (tools/gfx.py), rasterised, no antialiasing | none; letters scaled per box |
| (tools/gfx.py) PIXEL_FONT 3x7 capitals | drawn for this project | same as the repo | yes | book cover plaque | - |
| (ROM) 8x8 BG3 font at 0x40000 | the game's own | - | yes (part of the original) | credits, HUD, stage names (format A/B/C): uppercase A-Z, digits, punctuation | none |
