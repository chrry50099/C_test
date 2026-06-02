from pathlib import Path

from code_indexer.parser import CParser


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
FAKE_FW = WORKSPACE_ROOT / "Fake_FW"


def test_parser_extracts_functions_and_calls() -> None:
    parsed = CParser().parse_file(FAKE_FW / "nvme.c", "nvme.c")

    functions = {function.name for function in parsed.functions}
    calls = {(call.caller_name, call.callee_name) for call in parsed.calls}

    assert "nvme_submit_write" in functions
    assert ("nvme_submit_write", "scheduler_enqueue") in calls
    assert ("nvme_controller_init", "ftl_init") in calls


def test_parser_extracts_debug_hints() -> None:
    parsed = CParser().parse_file(FAKE_FW / "ftl.c", "ftl.c")

    hint_text = " ".join(hint.text for hint in parsed.debug_hints)
    assert "off-by-one" in hint_text
    assert "null buffer" in hint_text

