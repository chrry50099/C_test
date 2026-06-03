from pathlib import Path
import subprocess

from code_indexer.ctags import parse_ctags_json_lines, run_ctags


def test_parse_ctags_json_lines() -> None:
    lines = [
        '{"_type":"tag","name":"FW_PAGE_SIZE","path":"fw_types.h","line":7,"kind":"macro"}',
        '{"_type":"tag","name":"ssd_request","path":"fw_types.h","line":30,"kind":"struct"}',
        '{"_type":"tag","name":"ftl_write","path":"ftl.c","line":42,"kind":"function","signature":"(ftl_context_t *ftl)"}',
    ]

    symbols = parse_ctags_json_lines(lines, Path("."))

    assert [symbol.name for symbol in symbols] == ["FW_PAGE_SIZE", "ssd_request", "ftl_write"]
    assert symbols[2].kind == "function"
    assert symbols[2].signature == "(ftl_context_t *ftl)"


def test_run_ctags_uses_utf8_decoding(monkeypatch, tmp_path: Path) -> None:
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen.update(kwargs)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"_type":"tag","name":"測試符號","path":"main.c","line":1,"kind":"function"}\n',
            stderr="",
        )

    monkeypatch.setattr("code_indexer.ctags._resolve_executable", lambda _executable: "ctags")
    monkeypatch.setattr("code_indexer.ctags.subprocess.run", fake_run)

    symbols = run_ctags(tmp_path)

    assert seen["encoding"] == "utf-8"
    assert seen["errors"] == "replace"
    assert symbols[0].name == "測試符號"
