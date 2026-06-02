from __future__ import annotations

import hashlib
from pathlib import Path

from code_indexer.models import SourceFile

C_SOURCE_EXTENSIONS = {".c", ".h"}
IGNORED_DIRS = {".git", ".hg", ".svn", ".venv", "build", "__pycache__"}


def discover_c_files(repo_root: Path | str) -> list[SourceFile]:
    root = Path(repo_root).resolve()
    files: list[SourceFile] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in C_SOURCE_EXTENSIONS:
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue

        data = path.read_bytes()
        stat = path.stat()
        rel_path = path.relative_to(root).as_posix()
        files.append(
            SourceFile(
                path=path,
                rel_path=rel_path,
                module=module_name(rel_path),
                sha256=hashlib.sha256(data).hexdigest(),
                mtime=stat.st_mtime,
                size=stat.st_size,
            )
        )

    return files


def module_name(rel_path: str) -> str:
    path = Path(rel_path)
    if path.parent == Path("."):
        return path.stem
    return path.parent.as_posix().replace("/", ".")

