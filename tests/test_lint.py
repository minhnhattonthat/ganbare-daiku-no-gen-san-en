"""Text lint over script/ (phase 7): layout codes only and one {end}, credits keep their {br} layout, no Japanese
left in `en`, untranslated text only by keep-list, leading/trailing blanks as in the JP, no stub last line, and the
glossary's EN form present / Avoid forms absent. Width and lines: tests/test_fit.py."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import fit  # noqa: E402
import script  # noqa: E402

CODES = {"{nl}", "{br}", "{half}", "{kana}", "{page}", "{end}"}
JP = re.compile(r"[぀-ヿ一-鿿｡-ﾟ]")
KEEP = {line.split()[0] for line in (ROOT / "script" / "keep_jp.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")}


def filled():
    return [e for e in script.entries() if e["kind"] == "text" and e["en"]]


def test_codes():
    for e in filled():
        assert set(re.findall(r"\{[^}]*\}|\[[0-9A-F]{2}\]", e["en"])) <= CODES, e["name"]
        assert e["en"].count("{end}") == 1 and e["en"].endswith("{end}"), e["name"]
        if e["name"].startswith("credit"):
            assert e["en"].count("{br}") == e["jp"].count("{br}"), e["name"]


def test_no_japanese_in_en():
    assert not [e["name"] for e in filled() if JP.search(e["en"])]


def test_untranslated_only_by_keep_list():
    blank = {e["name"] for e in script.entries() if e["kind"] == "text" and not e["en"]}
    assert blank == KEEP, f"untranslated, not in script/keep_jp.txt: {blank - KEEP}; kept but filled: {KEEP - blank}"


def test_edge_blanks_match():
    for e in filled():
        j, n = e["jp"].removesuffix("{end}"), e["en"].removesuffix("{end}")
        assert (j[:1] == " ", j[-1:] == " ") == (n[:1] == " ", n[-1:] == " "), e["name"]


def test_no_stub_last_line():
    for e in filled():
        if fit.WINDOWS.get(fit.box_of(e["name"]), {}).get("short"):  # boxes too narrow for a 6-letter line rule
            continue
        for part in e["en"].removesuffix("{end}").split("{page}"):
            ls = [s for s in (re.sub(r"\{[^}]*\}", "", x).strip() for x in re.split(r"\{nl\}|\{br\}", part)) if s]
            assert len(ls) < 2 or len(ls[-1]) >= 6, f"{e['name']}: stub last line {ls[-1]!r}"


def test_glossary():
    for e in filled():
        low = e["en"].lower()
        for t, forms, line in batches.terms_in(e["jp"]):
            assert any(f.lower() in low for f in forms), f"{e['name']}: {t} -> {forms}"
            avoid = [a.strip() for a in line.strip().strip("|").split("|")[-1].split(",") if a.strip()]
            assert not [a for a in avoid if re.search(rf"\b{re.escape(a)}(?![-\w])", e["en"], re.I)], f"{e['name']}: {avoid}"
