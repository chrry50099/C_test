from pathlib import Path

from code_indexer.api import build_index, open_index


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
FAKE_FW = WORKSPACE_ROOT / "Fake_FW"


def test_build_index_creates_queryable_database(tmp_path: Path) -> None:
    db_path = tmp_path / "index.sqlite"

    stats = build_index(FAKE_FW, db_path, ctags_executable="definitely-missing-ctags")

    assert stats.files == 20
    assert stats.functions >= 25
    assert stats.calls >= 20
    assert stats.symbols >= stats.functions
    assert stats.ctags_used is False

    with open_index(db_path) as db:
        symbols = db.get_symbol("ftl_write")
        callers = db.get_callers("nand_program_page")
        callees = db.get_callees("nvme_submit_write")
        hints = db.get_debug_hints()

    assert symbols
    assert any(call.caller_name == "ftl_write" for call in callers)
    assert any(call.callee_name == "scheduler_enqueue" for call in callees)
    assert len(hints) >= 5

