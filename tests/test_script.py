"""script/*.json: holds every ROM string exactly once with its current ROM text, every filled `en` encodes, an untranslated
script builds the original ROM, and a re-dump keeps the translations."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import script  # noqa: E402
from tbl import Table  # noqa: E402
from text_map import EN_TABLES, ROM, layout, scan, sid, texts  # noqa: E402

needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="no ROM dump in rom/")


@pytest.fixture(scope="module")
def rom():
    return ROM.read_bytes()


@needs_rom
def test_script_matches_rom(rom):
    items, _ = scan(rom)
    ids = [e["id"] for e in script.entries()]
    assert len(ids) == len(set(ids)), "an id is in script/ twice"
    assert {e["id"]: e["jp"] for e in script.entries()} == texts(rom, items), "script/ is stale: re-run script.py dump"


def test_en_encodes():
    tables = {k: Table.load(ROOT / "tbl" / v) for k, v in EN_TABLES.items()}
    for e in script.entries():
        assert e["kind"] in ("text", "data"), e["id"]
        if e["en"]:
            assert e["en"].endswith("{end}"), f"{e['id']}: en must end in {{end}}"
            t = tables[e["id"][0]]
            assert t.decode(t.encode(e["en"]))[0] == e["en"], f"{e['id']}: en has characters the table lacks"


@needs_rom
def test_untranslated_script_builds_original(rom):
    items, refs = scan(rom)
    blank = {e["id"]: e["jp"] for e in script.entries()}
    assert layout(rom, items, refs, texts(rom, items) | blank)[0] == rom


@needs_rom
def test_dump_keeps_en(rom, tmp_path, monkeypatch):
    for f in script.DIR.glob("*.json"):
        (tmp_path / f.name).write_bytes(f.read_bytes())
    monkeypatch.setattr(script, "DIR", tmp_path)
    rows = script.read("cards")
    rows[0]["en"] = "X{end}"
    (tmp_path / "cards.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    script.dump(rom)
    assert script.read("cards")[0]["en"] == "X{end}"
    assert script.text()[rows[0]["id"]] == "X{end}"
    items, _ = scan(rom)
    assert sid(next(i for i in items.values() if i.name == "card0")) == rows[0]["id"]
