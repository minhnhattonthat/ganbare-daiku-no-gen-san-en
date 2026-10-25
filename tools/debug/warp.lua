-- Cold-boot warp to a scene from tools/debug/scenes.lua, through the game's leftover debug stage select.
--   emu.py ROM --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='s2_boss'" --frames 900 --sheet
-- How: 7E:ED03 != 0 makes the stage-start check (C2:21E7) open the stage select (C2:2200) instead of the normal
-- flow. Its menu draws on a layer the main screen leaves off, so it is driven blind: once its loop (C2:226C)
-- runs, set the row (direct page $10) and press A; the game stores stage/checkpoint (7E:ECC7/ECC9) and starts it.
-- Globals: SCENE (required), GOD=1 (refill energy every frame), ADV=n (press A every n frames once in the scene:
-- pages through story text and the ending), SCENES_FILE (default: beside the repo's Mesen).
-- Logs "WARP <scene> live f<n>" once the stage runs, "WARP FAIL ..." otherwise.
local m = emu.memType.snesMemory
dofile(SCENES_FILE or "../debug/scenes.lua")  -- Mesen runs with cwd = tools/mesen
if LIST then  -- LIST=1: log the scene names (tools/debug/run_all.py reads them) and stop
  local names = {}
  for k in pairs(SCENES) do names[#names + 1] = k end
  table.sort(names)
  L.log("SCENES " .. table.concat(names, " "))
  L.finish()
  return
end
local sc = SCENES[SCENE]
if not sc then error("unknown SCENE " .. tostring(SCENE)) end

local phase, live, redirected = "boot", 0, false  -- boot -> menu -> picked -> live; live = frame the menu exited
L.on_frame(function(n)
  if GOD and phase == "live" then emu.write(0x7EECD5, 0x50, m) end  -- energy (cheat DB: 7EECD550)
  if phase == "boot" then
    emu.write(0x7EED03, 1, m)
    if n % 40 == 0 then L.press("start", 4); L.press("-", 2) end  -- through title, file book, intro, story pages
    if n > 6000 then error("WARP FAIL " .. SCENE .. ": no stage select by f6000") end
  end
  if phase ~= "live" then return end
  if ADV and (n - live) % ADV == 0 then L.press("a", 4) end
  if sc.after then sc.after(n - live, m) end
end)
L.on_exec(0xC2226C, 0xC2226C, function()
  if phase ~= "boot" then return end
  phase = "menu"
  emu.write(emu.getState()["cpu.d"] + 0x10, sc.row, m)
  L.press("-", 8); L.press("a", 4)
end)
L.on_exec(0xC222A8, 0xC222A8, function()  -- confirm path: the row about to be started
  if phase ~= "menu" then return end
  local row = emu.read(emu.getState()["cpu.d"] + 0x10, m)
  if row ~= sc.row then error(string.format("WARP FAIL %s: picked row %d, want %d", SCENE, row, sc.row)) end
  phase = "picked"
  emu.write(0x7EED03, 0, m)  -- back to the normal flow for stage clears and later stages
end)
-- Flow redirect: C2:0021 steps the flow graph to successor 7E:0044 of node 7E:0042 (docs/re/flow.md). A scene with
-- go = {node, index} leaves the menu into that successor instead of the stage start, e.g. {0x8053, 0} = stage clear.
L.on_exec(0xC20021, 0xC20021, function()
  if phase ~= "live" or not sc.go or redirected then return end
  redirected = true
  emu.write16(0x7E0042, sc.go[1], m); emu.write16(0x7E0044, sc.go[2], m)
end)
L.on_exec(0xC20045, 0xC20045, function()
  if phase ~= "picked" then return end
  phase, live = "live", L.frame
  L.log(string.format("WARP %s live f%d stage=%d chk=%d", SCENE, L.frame, emu.read(0x7EECC7, m), emu.read(0x7EECC9, m)))
end)
