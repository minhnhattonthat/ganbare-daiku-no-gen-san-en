"""tools/fit.py: every filled `en` fits its measured box (data/windows.json), and every text entry has a box."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fit  # noqa: E402
import script  # noqa: E402

NO_BOX = {"title10E2", "title10EE"}  # title bubble: redrawn with the title graphics, no text box


def test_every_text_entry_has_a_box():
    missing = [e["name"] for e in script.entries()
               if e["kind"] == "text" and e["name"] not in NO_BOX and fit.box_of(e["name"]) is None]
    assert not missing


def test_filled_en_fits():
    assert fit.lint() == 0


def test_problems():
    assert fit.problems("123456789012345678{end}", "panel") == []
    assert fit.problems("1234567890123456789{end}", "panel")
    assert fit.problems("a{nl}b{nl}c{nl}d{page}e{end}", "panel") == []
    assert fit.problems("a{nl}b{nl}c{nl}d{nl}e{end}", "panel")
    assert fit.problems("a{page}b{end}", "page")
    assert fit.problems("Mikami{end}", "credit")
