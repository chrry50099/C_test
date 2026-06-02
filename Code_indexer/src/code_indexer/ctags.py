from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from code_indexer.models import Symbol


class CtagsUnavailable(RuntimeError):
    pass


def run_ctags(repo_root: Path | str, executable: str = "ctags") -> list[Symbol]:
    root = Path(repo_root).resolve()
    exe = _resolve_executable(executable)
    if exe is None:
        raise CtagsUnavailable(f"Universal Ctags executable was not found: {executable}")

    command = [
        exe,
        "--output-format=json",
        "--languages=C",
        "--fields=+nKSt",
        "--kinds-C=+defgmpstuvx",
        "-R",
        "-f",
        "-",
        ".",
    ]
    result = subprocess.run(command, cwd=root, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise CtagsUnavailable(result.stderr.strip() or "ctags failed")

    return parse_ctags_json_lines(result.stdout.splitlines(), root)


def _resolve_executable(executable: str) -> str | None:
    candidate = Path(executable)
    if candidate.is_absolute() or "\\" in executable or "/" in executable:
        return str(candidate) if candidate.exists() else None
    return shutil.which(executable)


def parse_ctags_json_lines(lines: list[str], repo_root: Path | str) -> list[Symbol]:
    root = Path(repo_root).resolve()
    symbols: list[Symbol] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if payload.get("_type") != "tag":
            continue

        path_value = payload.get("path") or payload.get("input")
        if not path_value:
            continue
        path = Path(path_value)
        if path.is_absolute():
            rel_path = path.resolve().relative_to(root).as_posix()
        else:
            rel_path = path.as_posix().lstrip("./")

        symbols.append(
            Symbol(
                name=payload.get("name", ""),
                kind=payload.get("kind", payload.get("kindName", "")),
                path=rel_path,
                line=_int_or_none(payload.get("line")),
                column=_int_or_none(payload.get("column")),
                signature=payload.get("signature") or payload.get("pattern"),
                scope=payload.get("scope") or payload.get("scopeName"),
                source="ctags",
            )
        )

    return symbols


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
