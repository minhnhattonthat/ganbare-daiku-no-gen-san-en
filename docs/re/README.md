# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| [text.md](text.md) | font, format A strings (JIS X 0201 via C0:9411), stage names, HUD tilemap, every text location | verified (font F7/FA/FB unread) |
| [rom.md](rom.md) | header, free space (none), 7E:9000 WRAM copy, RLE compression, debug-menu flags | verified (debug flags not run yet) |
| [graphics.md](graphics.md) | graphics-text survey | partial: mid-game screens wait for the phase-2 warp tool |
