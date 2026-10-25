-- Scene list for tools/debug/warp.lua. Each entry: name = { row = <debug stage-select row 0-21> } (the leftover
-- menu at C2:2200, labels at file 0x1236, stage/checkpoint per row in the table at file 0x120A), plus optional
-- `after` = a function(L) run each frame once the stage is live, for scenes past the stage start.
SCENES = {
  s1a_chk0 = { row = 0 },  s1a_chk1 = { row = 1 },  s1a_chk2 = { row = 2 },
  s1b = { row = 3 },       s1_boss = { row = 4 },
  s2a_chk0 = { row = 5 },  s2a_chk1 = { row = 6 },  s2a_chk2 = { row = 7 },
  s2b_chk0 = { row = 8 },  s2b_chk1 = { row = 9 },  s2b_chk2 = { row = 10 },
  s2_boss = { row = 11 },
  s3a = { row = 12 },      s3b_chk0 = { row = 13 }, s3b_chk1 = { row = 14 },
  s3_boss = { row = 15 },
  s4a_chk0 = { row = 16 }, s4a_chk1 = { row = 17 }, s4b_chk0 = { row = 18 }, s4b_chk1 = { row = 19 },
  s4_boss = { row = 20 },
  final = { row = 21 },
}

local mem = emu.memType.snesMemory
-- Cheat-DB addresses (libretro-database Action Replay .cht): lives 7E:ECCB, energy 7E:ECD5, 7E:0298 = $13 makes
-- enemies pass through, 7E:1748 = 9 and 7E:ECD3 = 9 max hammer power.
local function strong()
  emu.write(0x7E0298, 0x13, mem); emu.write(0x7E1748, 9, mem); emu.write(0x7EECD3, 9, mem)
end
-- No lives, no energy, walk right into the first enemy: death, then game over. (Energy 0 alone kills nobody.)
SCENES.gameover = { row = 0, after = function(t)
  if t < 120 then return end
  emu.write(0x7EECCB, 0, mem); emu.write(0x7EECD5, 0, mem)
  if t % 30 == 0 then L.press("right", 30) end
end }
-- Flow-graph scenes (docs/re/flow.md): pick a row, then leave the menu into another node instead of the stage.
-- {0x8053, 0} = stage clear of the row's stage (C2:5DC9 steps 7E:ECC7 and picks map / $807A / ending),
-- {0x8053, 2} = continue screen.
-- clear_<n> = after stage value n (7E:ECC7: 1 = stage 1 first half ... 13 = FINAL): the story pages and map before
-- stage n+1; clear_10 goes through the teleporter cutscene ($807A), clear_13 is the ending and staff roll.
SCENES.continue = { row = 0, go = { 0x8053, 2 } }
local first_row = { 0, 3, 4, 5, 8, 11, 12, 13, 15, 16, 18, 20, 21 }  -- first menu row with stage value 1..13
for n, row in ipairs(first_row) do SCENES["clear_" .. n] = { row = row, go = { 0x8053, 0 } } end
SCENES.ending = SCENES.clear_13
