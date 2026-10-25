"""Warp to every scene in tools/debug/scenes.lua from a cold boot: one shot and one savestate per scene.

    python -X utf8 tools/debug/run_all.py [ROM] [--only s2_boss,ending] [--frames 2000] [--jobs 4]

Each scene runs `emu.py ROM --script tools/debug/warp.lua --var SCENE='<name>'` to --frames, keeps final.png as
work/qa/scenes/<name>.png, saves work/states/<name>.mss, and fails unless the log shows "WARP <name> live"
(the stage select was reached and left with the right row). Writes work/qa/scenes/sheet.png. Exit 1 on any failure.
Regenerate the states after any engine, font or graphics change: savestates carry the old code and VRAM.
"""
import argparse, os, re, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skill import SKILL  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EMU = os.path.join(SKILL, "scripts", "emu.py")
WARP = os.path.join(ROOT, "tools", "debug", "warp.lua")


def emu(rom, out, *args):
    return subprocess.run([sys.executable, "-X", "utf8", EMU, rom, "--out", out, "--script", WARP, *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def scene_names(rom):
    out = os.path.join(ROOT, "work", "qa", "scenes", "_list")
    r = emu(rom, out, "--var", "LIST=1", "--frames", "10")
    log = open(os.path.join(out, "log.txt"), encoding="utf-8").read()
    m = re.search(r"^SCENES (.+)$", log, re.M)
    if not m:
        sys.exit(f"no scene list: {r.stdout}{r.stderr}")
    return m.group(1).split()


def run(rom, name, frames):
    out = os.path.join(ROOT, "work", "qa", "scenes", name)
    state = os.path.join(ROOT, "work", "states", name + ".mss")
    r = emu(rom, out, "--var", f"SCENE='{name}'", "--frames", str(frames), "--state-out", state)
    log = open(os.path.join(out, "log.txt"), encoding="utf-8").read() if os.path.exists(os.path.join(out, "log.txt")) else ""
    ok = r.returncode == 0 and f"WARP {name} live" in log and os.path.exists(os.path.join(out, "final.png"))
    if ok:
        shutil.copy(os.path.join(out, "final.png"), os.path.join(ROOT, "work", "qa", "scenes", name + ".png"))
    return name, ok, (r.stdout + r.stderr).strip().splitlines()[-1:] if not ok else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", default=os.path.join(ROOT, "rom", "Ganbare! Daiku no Gen-san (Japan).sfc"))
    ap.add_argument("--only", help="comma-separated scene names")
    ap.add_argument("--frames", type=int, default=2000)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(os.path.join(ROOT, "work", "states"), exist_ok=True)
    names = a.only.split(",") if a.only else scene_names(a.rom)
    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(lambda n: run(a.rom, n, a.frames), names))
    bad = [r for r in results if not r[1]]
    for name, ok, msg in results:
        print(("ok   " if ok else "FAIL ") + name, msg or "")
    good = [os.path.join(ROOT, "work", "qa", "scenes", n + ".png") for n, ok, _ in results if ok]
    if good:
        subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "sheet.py"), *good,
                        "--max", "40", "--out", os.path.join(ROOT, "work", "qa", "scenes", "sheet.png")])
    print(f"{len(results) - len(bad)}/{len(results)} scenes reached")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
