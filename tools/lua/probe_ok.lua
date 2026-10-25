-- Step 0 check: proves a --script probe's L.log reaches log.txt.
L.on_frame(function(n) if n == 100 then L.log("probe ok frame 100") end end)
