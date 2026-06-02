from code_indexer.toolchain import run_doctor


def test_doctor_reports_tool_status_without_crashing() -> None:
    statuses = run_doctor()
    names = {status.name for status in statuses}

    assert {"ctags", "cmake", "clang", "clangd", "libclang"}.issubset(names)
    assert all(isinstance(status.ok, bool) for status in statuses)

