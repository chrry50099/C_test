from pathlib import Path

from code_indexer.cli import main


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
FAKE_FW = WORKSPACE_ROOT / "Fake_FW"


def test_cli_scan_summary_and_query(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "index.sqlite"

    assert main(["scan", str(FAKE_FW), "--db", str(db_path), "--ctags", "definitely-missing-ctags"]) == 0
    scan_out = capsys.readouterr().out
    assert "files=203" in scan_out
    assert "ctags=not-used" in scan_out
    assert "elapsed command=scan seconds=" in scan_out

    assert main(["summary", "--db", str(db_path)]) == 0
    summary_out = capsys.readouterr().out
    assert "functions:" in summary_out
    assert "elapsed command=summary" not in summary_out

    assert main(["callees", "nvme_submit_write", "--db", str(db_path)]) == 0
    callees_out = capsys.readouterr().out
    assert "scheduler_enqueue" in callees_out

    assert main(["debug-hints", "--db", str(db_path)]) == 0
    hints_out = capsys.readouterr().out
    assert "BUG_HINT" not in hints_out
    assert "off-by-one" in hints_out
