"""tools/engine.py + moved text blocks: the normal and the marker build pass romdiff (every patch found its original
bytes, no write overlaps another), moved blocks stay inside their slot, and the stage-name hook's branches land."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import engine  # noqa: E402
from text_map import BLOCKS, ROM, SLOT, layout, scan, sid, texts, u16, u24  # noqa: E402

needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="no ROM dump in rom/")


@pytest.fixture(scope="module")
def rom():
    return ROM.read_bytes()


@needs_rom
@pytest.mark.parametrize("args", [[], ["--marker"]])
def test_build_passes_romdiff(args, tmp_path):
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "build.py"), *args, "--out", str(tmp_path / "t.sfc")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    out = (tmp_path / "t.sfc").read_bytes()
    for lo, hi, what, _ in BLOCKS:  # moved: no Japanese left behind at the old offsets
        assert out[lo:hi] == b"\xff" * (hi - lo), what


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("b") / "t.sfc"
    subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "build.py"), "--out", str(out)], check=True,
                   capture_output=True)
    return out.read_bytes()


# long operands into a moved block that the build leaves alone: all in data (C2:A6E8 sits in BRK/garbage bytes, the
# rest in the graphics/data banks); textlog.lua showed every renderer pointer comes from the scanned tables
LONG_DATA = {0x2A6E8, 0x5020A, 0x72EF4, 0x7B1D1, 0xB0B00, 0xC3E9F, 0xEFF60, 0xF37E6, 0xF5F79, 0xF873B, 0xFBB2C,
             0xFEA60}


@needs_rom
def test_no_stale_reader(rom, built):
    """Byte sweep of the original for readers of a vacated block: every long operand (LDA $C2xxxx.., JSL/JML) and
    every LDX/LDY/LDA #lo next to an LDY #$00Cn bank load must be rewritten by the build (or be known data)."""
    def block(f):
        return any(lo <= f < hi for lo, hi, *_ in BLOCKS)
    stale = []
    for p in range(len(rom) - 3):
        if rom[p] & 0x0F == 0x0F or rom[p] in (0x22, 0x5C):
            a = int.from_bytes(rom[p + 1:p + 4], "little")
            # shortcut: banks C0-C3/40-43 only (every known text reader uses C0-C3); 00-03/80-83 mirrors add ~40 data
            # hits, triage them if a reader through a mirror ever turns up
            if a >> 16 in (*range(0xC0, 0xC4), *range(0x40, 0x44)):
                if block(a & 0x3FFFFF) and built[p + 1:p + 4] == rom[p + 1:p + 4] and p not in LONG_DATA:
                    stale.append(f"{p:06X} long")
        if rom[p] in (0xA0, 0xA2, 0xA9) and rom[p + 2] == 0 and rom[p + 1] in range(0xC0, 0xC4):
            for q in range(p - 12, p + 12):
                if q != p and rom[q] in (0xA0, 0xA2, 0xA9) and block((rom[p + 1] & 0x3F) << 16 | u16(rom, q + 1)):
                    if built[p + 1] == rom[p + 1] or built[q + 1:q + 3] == rom[q + 1:q + 3]:
                        stale.append(f"{p:06X} bank/{q:06X} lo")
    assert not stale


@needs_rom
def test_no_branch_into_a_hook(rom):
    """Byte scan +-4 KB around each patched code span (data included, so it over-reports): no branch, jump or call
    lands strictly inside a span."""
    spans = [(o, len(a)) for o, a, _, why in engine.PATCHES if why[:3] in ("C0:", "C2:") and "cue" not in why]
    rel = {0x10, 0x30, 0x50, 0x70, 0x80, 0x90, 0xB0, 0xD0, 0xF0}
    hits = []
    for o, n in spans:
        for p in range(o - 4096, o + n + 4096):
            b, t = rom[p], None
            if b in rel:
                t = p + 2 + int.from_bytes(rom[p + 1:p + 2], "little", signed=True)
            elif b == 0x82:  # BRL
                t = p + 3 + int.from_bytes(rom[p + 1:p + 3], "little", signed=True)
            elif b in (0x4C, 0x20):  # JMP/JSR abs, same bank
                t = p & 0xFF0000 | int.from_bytes(rom[p + 1:p + 3], "little")
            elif b in (0x5C, 0x22):  # JML/JSL long, HiROM C0-
                t = int.from_bytes(rom[p + 1:p + 4], "little") - 0xC00000
            if t is not None and o < t < o + n:
                hits.append(f"{p:06X} -> {t:06X}")
    assert len(spans) == 7 and not hits


@needs_rom
def test_page_splits_a_panel(rom):
    """{page} in an English panel line repeats its script entry (same layout bytes) with the second part."""
    items, refs = scan(rom)
    text = texts(rom, items)
    s3 = next(i for i in items.values() if i.name == "script3")
    target = next(i for i in items.values() if i.name == "script3.2")
    text[sid(target)] = "AB{page}CD{end}"
    out, _ = layout(rom, items, refs, text, en={sid(target)})
    tbl = u24(out, u24(out, 0x1FB52) + 3 * 3)  # script table entry 3 -> script3's entry table
    assert out[tbl] == rom[s3.off] + 1
    e2, e3 = out[tbl + 1 + 22:tbl + 1 + 33], out[tbl + 1 + 33:tbl + 1 + 44]
    assert e2[3:] == e3[3:] == rom[s3.off + 1 + 22 + 3:s3.off + 1 + 33]
    head = bytes([target.head[0] // 2]) + target.head[1:]
    assert out[u24(e2, 0):u24(e2, 0) + 7] == head + bytes([0x21, 0x22, 0xFF])
    assert out[u24(e3, 0):u24(e3, 0) + 7] == head + bytes([0x23, 0x24, 0xFF])


def test_moves_fit_slots():
    assert set(engine.MOVES) == {lo for lo, *_ in BLOCKS}
    slots = sorted(engine.MOVES.values())
    assert slots[0] >= engine.CODE + SLOT and slots[-1] + SLOT <= engine.SIZE
    assert all(s % SLOT == 0 for s in slots) and len(set(slots)) == len(slots)


def test_stage_hook_branches():
    code = engine.stage_name(0xD0)
    beq = code.index(b"\xf0")
    assert code[beq + 2 + code[beq + 1]] == 0xAB  # BEQ -> PLB before the JML back
    bra = code.index(b"\x80", beq)
    assert bra + 2 + code[bra + 1] - 0x100 == code.index(bytes.fromhex("b90000"))  # BRA -> LDA $0000,y
    assert code.endswith(bytes.fromhex("5c2913c2"))


def test_font_glyphs():
    g = engine.glyphs()
    assert sorted(g) == list(range(0x5F)) and all(len(r) == 16 for r in g.values())
