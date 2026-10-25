-- Log every story-text (format D) string the game draws: typewriter C2:0F63 (Y:X = ptr24) and instant C2:0EBF.
--   emu.py ROM --script tools/debug/warp.lua --var "SCENE='clear_3'" --var ADV=40 --script tools/lua/textlog.lua
-- Lines: "TEXT f<frame> type|inst <ptr24> from <caller>" (caller from the JSL return address on the stack).
local m = emu.memType.snesMemory
local function caller()
  local sp = emu.getState()["cpu.sp"]
  local lo = emu.read(sp + 1, m) | emu.read(sp + 2, m) << 8
  return string.format("%02X%04X", emu.read(sp + 3, m), (lo - 3) & 0xFFFF)
end
local function hook(kind)
  return function()
    local s = emu.getState()
    L.log(string.format("TEXT f%d %s %02X%04X from %s", L.frame, kind, s["cpu.y"] & 0xFF, s["cpu.x"], caller()))
  end
end
L.on_exec(0xC20F63, 0xC20F63, hook("type"))
L.on_exec(0xC20EBF, 0xC20EBF, hook("inst"))
