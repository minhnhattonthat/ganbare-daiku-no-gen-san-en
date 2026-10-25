"""tools/engine.py + moved text blocks: the normal and the marker build pass romdiff (every patch found its original
bytes, no write overlaps another), moved blocks stay inside their slot, and the stage-name hook's branches land."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import engine  # noqa: E402
from text_map import BLOCKS, ROM, SLOT, layout, scan, sid, texts, u24  # noqa: E402

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
