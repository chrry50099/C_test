from pathlib import Path

from code_indexer.ctags import parse_ctags_json_lines


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

