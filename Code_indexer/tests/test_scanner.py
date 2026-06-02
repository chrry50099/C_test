from pathlib import Path

from code_indexer.scanner import discover_c_files


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
FAKE_FW = WORKSPACE_ROOT / "Fake_FW"


def test_discover_c_files_finds_fake_fw_sources() -> None:
    files = discover_c_files(FAKE_FW)
    paths = {file.rel_path for file in files}

    assert len(files) == 21
    assert "main.c" in paths
    assert "conf.h" in paths
    assert "nvme.h" in paths
