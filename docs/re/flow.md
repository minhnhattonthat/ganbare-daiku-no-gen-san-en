# Game flow graph (verified: every node below reached by `tools/debug/run_all.py`)

The game's top level is a graph of nodes at file 0x15-0x8C, copied to **7E:8015-808C** at boot (file 0x0000.. ->
7E:8000..). Node = 3-byte handler address, then successor node words (successor k at node+3+2k).
A handler ends with `LDA #k; JML C2:0045`; C2:0045 stores k in 7E:0044 and schedules C2:0021, which sets
7E:0042 = successor k of node 7E:0042 and runs its handler. `tools/debug/warp.lua` redirects the flow by writing
7E:0042/0044 when C2:0021 runs (scene field `go = {node, k}`).

| Node | Handler | Successors | What |
|---|---|---|---|
| 8015 | C2:1687 | 801A | boot |
| 801A | C0:8000 | 801F | irem logo |
| 801F | C2:18F8 | 8024 | |
| 8024 | C2:191E | 8030, 802B | title / file book |
| 802B | C2:23A4 | 804E | guess: password/continue entry from the file book (sets ECC7/ECC9 from table C3:4A8D) |
| 8030 | C2:5D39 | 8035 | new game: stage 1, lives 2 (7E:ECCB), energy $50 (7E:ECD5) |
| 8035 | C2:33E3 | 803A | intro (house, NEW letters) |
| 803A | C2:482F | 803F | |
| 803F | C1:F69E | 8044 | story book pages for the coming stage |
| 8044 | C2:2AE1 | 8049 | map with chapter label |
| 8049 | C2:21E7 | 804E | stage-start check: 7E:ED03 != 0 or 7E:ECE9 == 1 -> debug stage select C2:2200 |
| 804E | C2:5D79 | 8053 | stage init (7E:ECC7 stage 1-13, 7E:ECC9 checkpoint) |
| 8053 | C2:6001 | 805E, 8067, 806E, 8024 | stage play: 0 clear, 1 death, 2 game over, 3 quit |
| 805E | C2:5DC9 | 803F, 807A, 8075 | stage clear: INC 7E:ECC7, successor from C2:5DBA[ECC7] (11 -> 807A, 14 -> 8075) |
| 8067 | C2:5E03 | 8049, 8024 | death: lives - 1, retry |
| 806E | C2:3AA7 | 8049, 8024 | continue screen (two signposts) |
| 8075 | C2:2548 | 807A | after FINAL: ending dialogue |
| 807A | C2:40AA | 8044, 8083, 8088 | teleporter cutscene (after stage 10) / ending branch |
| 8083 | C2:2FA4 | 8088 | ending |
| 8088 | C2:33EB | 8024 | staff roll |

Handlers' roles marked blank are unconfirmed; the ones named were seen in warp shots (`work/qa/scenes/`).

Debug stage select (C2:2200): 22 rows (labels file 0x1236, table 7E:91DE), row in direct page $10, Up/Down move,
A or Start picks; table file 0x120A gives stage (lo) / checkpoint (hi) per row, stored to 7E:ECC7 / ECC9.
Its text draws on a layer the main screen keeps off except for a flash, so warp.lua drives it blind.

Cheat-DB RAM (libretro-database Action Replay .cht, verified in warp runs): lives 7E:ECCB (BCD), energy 7E:ECD5
(max $50; 0 only kills on the next hit), 7E:0298 = $13 enemies pass through, 7E:1748 / 7E:ECD3 hammer power.
