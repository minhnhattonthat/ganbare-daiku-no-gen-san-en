"""tools/batches.py: the one-line batch form maps back to the script's control codes."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402


def test_roundtrip_keeps_box_codes():
    # panels with {nl}{half} (2 of them) come back as plain {nl}; credits lose {kana}: both on purpose
    for b in batches.BATCHES:
        for e in batches.entries(b):
            if "{kana}" in e["jp"] or (batches.box(e) == "panel" and "{half}" in e["jp"]):
                continue
            assert batches.from_tsv(e, batches.to_tsv(e)) == e["jp"], e["name"]


def test_terms_mask_longer_names():
    found = [t for t, _, _ in batches.terms_in("源三くん！源さん")]
    assert "源三" in found and "源さん" in found and "源" not in found
