-- Log every call of the RLE decompressor (C2:01EA): frame, source block (file offset) and WRAM destination (Y).
--   emu.py ... --script tools/lua/decomp_log.lua
local mem = emu.memType.snesMemory
local seen = {}
L.on_exec(0xC201EA, 0xC201EA, function()
  local s = emu.getState()
  local d = s["cpu.d"]
  local src = emu.read(d + 0x12, mem) << 16 | emu.read(d + 0x11, mem) << 8 | emu.read(d + 0x10, mem)
  local key = src * 65536 + s["cpu.y"]
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("f%d decomp src=%06X off=%06X type=%d dst=%04X", L.frame, src, src & 0x3FFFFF,
    emu.read(src, mem), s["cpu.y"]))
end)
