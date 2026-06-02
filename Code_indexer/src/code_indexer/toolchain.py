from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolStatus:
    name: str
    ok: bool
    detail: str


def run_doctor(repo_root: Path | str | None = None, compile_commands: Path | str | None = None) -> list[ToolStatus]:
    statuses = [
        _tool_status("ctags"),
        _tool_status("cmake"),
        _tool_status("clang"),
        _tool_status("clangd"),
        _libclang_status(),
    ]
    if compile_commands is not None:
        path = Path(compile_commands)
    elif repo_root is not None:
        path = Path(repo_root) / "build" / "compile_commands.json"
    else:
        path = None

    if path is not None:
        statuses.append(ToolStatus("compile_commands", path.exists(), str(path)))
    return statuses


def _tool_status(name: str) -> ToolStatus:
    path = shutil.which(name)
    if path is None:
        return ToolStatus(name, False, "not found in PATH")
    return ToolStatus(name, True, path)


def _libclang_status() -> ToolStatus:
    try:
        from clang import cindex

        cindex.Index.create()
    except Exception as exc:
        return ToolStatus("libclang", False, f"{type(exc).__name__}: {exc}")
    return ToolStatus("libclang", True, "clang.cindex loaded")

