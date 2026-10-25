"""Text tour: warp to each scene from a cold boot, press A every ADV frames, shoot every --every frames, and keep a
contact sheet of the frames that changed. For the marker build and the QA tours.

    python -X utf8 tools/debug/tour.py [ROM] [--only clear_1,continue] [--out work/qa/tour] [--jobs 4]

Out: <out>/<scene>/f*.png, sheet*.png (sheet.py --changed). Exit 1 if a warp failed.
"""
import argparse, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skill import SKILL  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARP = os.path.join(ROOT, "tools", "debug", "warp.lua")
# scene -> frames: every scene that draws text (story pages, cards, dialogue, ending, staff roll, continue, HUD)
SCENES = {f"clear_{n}": 4500 for n in range(1, 13)} | {"clear_13": 16000, "continue": 2500, "s1a_chk0": 1800,
                                                       "gameover": 3000}


def run(rom, out, name, frames, every, adv):
    d = os.path.join(out, name)
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), rom, "--out", d,
                        "--script", WARP, "--var", f"SCENE='{name}'", "--var", f"ADV={adv}",
                        "--frames", str(frames), "--shot-every", str(every)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = os.path.join(d, "log.txt")
    ok = r.returncode == 0 and os.path.exists(log) and f"WARP {name} live" in open(log, encoding="utf-8").read()
    if ok:
        subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "sheet.py"), d,
                        "--changed", "0.02"], capture_output=True)
    return name, ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", default=os.path.join(ROOT, "build", "gensan_en.sfc"))
    ap.add_argument("--only")
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "qa", "tour"))
    ap.add_argument("--every", type=int, default=60)
    ap.add_argument("--adv", type=int, default=90)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    names = a.only.split(",") if a.only else list(SCENES)
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda n: run(a.rom, a.out, n, SCENES.get(n, 3000), a.every, a.adv), names))
    for name, ok in res:
        print(("ok   " if ok else "FAIL ") + name)
    return 0 if all(ok for _, ok in res) else 1


if __name__ == "__main__":
    sys.exit(main())
