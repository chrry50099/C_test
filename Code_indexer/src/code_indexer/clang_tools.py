from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from code_indexer.compile_db import clang_args_for_unit, load_compile_database
from code_indexer.models import Diagnostic

CLANGD_DIAG_RE = re.compile(r"(?P<level>I|W|E)\[[^\]]+\] (?P<message>.*)")


def run_clangd_check(
    source_file: Path | str,
    compile_commands_dir: Path | str,
    *,
    clangd_executable: str = "clangd",
) -> list[Diagnostic]:
    clangd = _resolve_executable(clangd_executable)
    if clangd is None:
        return [
            Diagnostic(
                source="clangd",
                rel_path=str(source_file),
                line=None,
                column=None,
                severity="missing-tool",
                message=f"clangd executable was not found: {clangd_executable}",
                profile=None,
            )
        ]

    source = Path(source_file)
    command = [
        clangd,
        f"--check={source}",
        f"--compile-commands-dir={Path(compile_commands_dir)}",
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    return _parse_clangd_output(source, result.stdout + "\n" + result.stderr)


def run_libclang_scan(repo_root: Path | str, compile_commands: Path | str) -> list[Diagnostic]:
    try:
        from clang import cindex
    except Exception as exc:
        return [
            Diagnostic(
                source="libclang",
                rel_path="",
                line=None,
                column=None,
                severity="missing-python-binding",
                message=f"clang.cindex import failed: {exc}",
                profile=None,
            )
        ]

    root = Path(repo_root).resolve()
    units = load_compile_database(compile_commands, root)
    index = cindex.Index.create()
    diagnostics: list[Diagnostic] = []

    for unit in units:
        source_path = root / unit.rel_path
        if not source_path.exists():
            continue
        try:
            translation_unit = index.parse(str(source_path), args=clang_args_for_unit(unit))
        except Exception as exc:
            diagnostics.append(
                Diagnostic(
                    source="libclang",
                    rel_path=unit.rel_path,
                    line=None,
                    column=None,
                    severity="parse-error",
                    message=f"{type(exc).__name__}: {exc}",
                    profile=unit.profile,
                )
            )
            continue

        for diagnostic in translation_unit.diagnostics:
            location = diagnostic.location
            diagnostics.append(
                Diagnostic(
                    source="libclang",
                    rel_path=_relative_or_absolute(Path(str(location.file)), root) if location.file else unit.rel_path,
                    line=location.line or None,
                    column=location.column or None,
                    severity=_diagnostic_severity(cindex, diagnostic.severity),
                    message=diagnostic.spelling,
                    profile=unit.profile,
                )
            )

    return diagnostics


def _parse_clangd_output(source: Path, output: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for line in output.splitlines():
        match = CLANGD_DIAG_RE.search(line)
        if not match:
            continue
        severity = {"I": "info", "W": "warning", "E": "error"}.get(match.group("level"), "info")
        message = match.group("message")
        if "All checks completed" in message:
            continue
        diagnostics.append(
            Diagnostic(
                source="clangd",
                rel_path=source.as_posix(),
                line=None,
                column=None,
                severity=severity,
                message=message,
                profile=None,
            )
        )
    return diagnostics


def _diagnostic_severity(cindex, severity: int) -> str:
    if severity == cindex.Diagnostic.Ignored:
        return "ignored"
    if severity == cindex.Diagnostic.Note:
        return "note"
    if severity == cindex.Diagnostic.Warning:
        return "warning"
    if severity == cindex.Diagnostic.Error:
        return "error"
    if severity == cindex.Diagnostic.Fatal:
        return "fatal"
    return str(severity)


def _resolve_executable(executable: str) -> str | None:
    candidate = Path(executable)
    if candidate.is_absolute() or "\\" in executable or "/" in executable:
        return str(candidate) if candidate.exists() else None
    return shutil.which(executable)


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()

