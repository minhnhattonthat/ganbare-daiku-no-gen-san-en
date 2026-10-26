"""release.py: build -> tests -> smoke -> jp_left -> visual-QA gate -> checksum -> BPS (re-applied, compared) -> zip.

    python -X utf8 tools/release.py [--version 1.0] [--force]

Stops at the first failure. Writes release/GanbareDaikuNoGenSan_EN_v<version>.{bps,zip} + README.txt (local,
gitignored) and keeps the playable patched image in build/gensan_en_v<version>.sfc. Refuses to overwrite an existing
version's files without --force. The QA tour is tools/debug/tour.py; this script refuses a build whose sha1 differs
from the one that tour shot last (work/qa/tour/rom.sha1). The debug tool is Lua only (tools/debug/warp.lua), so no
debug code is ever in the ROM. Never publishes anything.
"""
import argparse
import hashlib
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SCRIPTS  # noqa: E402

ROM = ROOT / "rom" / "Ganbare! Daiku no Gen-san (Japan).sfc"
BUILT = ROOT / "build" / "gensan_en.sfc"
QA = ROOT / "work" / "qa"
NAME = "GanbareDaikuNoGenSan_EN"
PY = [sys.executable, "-X", "utf8"]
# Original text blocks (build/writes.txt) that the build vacates to FF: jp_left must find no Japanese left in them.
# ROM-wide scans are noise here (table codes reused by graphics, code and the English font; docs/status.md).
OLD_TEXT = {"jp.tbl": ["2B4EC-2B643", "2B846-2BA5C"],
            "story.tbl": ["23CEC-23D24", "2B643-2B83C", "2D836-2E0A0", "34ACB-34B88"]}


def run(*cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    if subprocess.run([*PY, *map(str, cmd)], cwd=ROOT).returncode:
        sys.exit(f"release: failed: {Path(str(cmd[0])).name}")


def hashes(data):
    return f"CRC32 {zlib.crc32(data):08X}, MD5 {hashlib.md5(data).hexdigest()}, SHA-1 {hashlib.sha1(data).hexdigest()}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--force", action="store_true", help="overwrite this version's existing release files")
    a = ap.parse_args()
    out = ROOT / "release"
    patch, zpath = out / f"{NAME}_v{a.version}.bps", out / f"{NAME}_v{a.version}.zip"
    if (patch.exists() or zpath.exists()) and not a.force:
        sys.exit(f"release: {patch.name} or {zpath.name} exists; pass --force to overwrite")

    run(ROOT / "build.py")
    run(ROOT / "tools" / "check.py")
    run(Path(SCRIPTS) / "emu.py", BUILT, "--out", QA / "smoke", "--route", ROOT / "tools" / "routes" / "boot.txt",
        "--smoke")
    for tbl, ranges in OLD_TEXT.items():
        run(Path(SCRIPTS) / "jp_left.py", BUILT, "--orig", ROM, "--tbl", ROOT / "tbl" / tbl,
            *[x for r in ranges for x in ("--range", r)])
    built = BUILT.read_bytes()
    shot = (QA / "tour" / "rom.sha1").read_text().strip() if (QA / "tour" / "rom.sha1").exists() else "none"
    if shot != hashlib.sha1(built).hexdigest():
        sys.exit(f"release: the QA tour shot build {shot}, not this one: run tools/debug/tour.py, then the visual-QA gate")
    run(Path(SCRIPTS) / "qa_gate.py", "check", QA / "manifest.tsv", QA / "verdicts")

    final = ROOT / "build" / f"gensan_en_v{a.version}.sfc"
    run(ROOT / "tools" / "bps.py", "snes-checksum", BUILT, "--out", final)
    out.mkdir(exist_ok=True)
    run(ROOT / "tools" / "bps.py", "make", ROM, final, patch)
    work = ROOT / "work" / "release"
    work.mkdir(parents=True, exist_ok=True)
    check = work / "reapplied.sfc"
    run(ROOT / "tools" / "bps.py", "apply", ROM, patch, check)
    if check.read_bytes() != final.read_bytes():
        sys.exit("release: the re-applied patch differs from the build")
    check.unlink()
    readme = (ROOT / "docs" / "README.release.txt").read_text(encoding="utf-8")
    readme = (readme.replace("{VERSION}", a.version).replace("{BASE}", hashes(ROM.read_bytes()))
              .replace("{PATCHED}", hashes(final.read_bytes())))
    (out / "README.txt").write_text(readme, encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(patch, patch.name)
        z.write(out / "README.txt", "README.txt")
    print(f"release: {zpath.relative_to(ROOT)} (patch sha1 {hashlib.sha1(patch.read_bytes()).hexdigest()}); "
          f"playable image {final.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
