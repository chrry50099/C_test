from __future__ import annotations

from pathlib import Path

from code_indexer.clang_tools import run_clangd_check, run_libclang_scan
from code_indexer.compile_db import load_compile_database
from code_indexer.ctags import CtagsUnavailable, run_ctags
from code_indexer.db import (
    IndexDb,
    initialize_database,
    insert_index,
    open_database,
    replace_compile_units,
    replace_diagnostics,
    tree_sitter_function_symbols,
)
from code_indexer.models import CallExpr, DebugHint, FunctionDef, IdentifierRef, IndexStats, Symbol
from code_indexer.parser import CParser
from code_indexer.scanner import discover_c_files


def build_index(
    repo_root: Path | str,
    db_path: Path | str,
    *,
    require_ctags: bool = False,
    ctags_executable: str = "ctags",
) -> IndexStats:
    root = Path(repo_root).resolve()
    files = discover_c_files(root)
    parser = CParser()

    functions: list[FunctionDef] = []
    calls: list[CallExpr] = []
    identifiers: list[IdentifierRef] = []
    debug_hints: list[DebugHint] = []

    for source_file in files:
        parsed = parser.parse_file(source_file.path, source_file.rel_path)
        functions.extend(parsed.functions)
        calls.extend(parsed.calls)
        identifiers.extend(parsed.identifiers)
        debug_hints.extend(parsed.debug_hints)

    symbols: list[Symbol] = tree_sitter_function_symbols(functions)
    ctags_used = False
    ctags_error: str | None = None

    try:
        ctags_symbols = run_ctags(root, executable=ctags_executable)
    except CtagsUnavailable as exc:
        ctags_error = str(exc)
        if require_ctags:
            raise
    else:
        symbols.extend(ctags_symbols)
        ctags_used = True

    conn = initialize_database(db_path)
    try:
        insert_index(conn, files, functions, calls, identifiers, symbols, debug_hints)
    finally:
        conn.close()

    return IndexStats(
        files=len(files),
        functions=len(functions),
        calls=len(calls),
        symbols=len(symbols),
        identifiers=len(identifiers),
        debug_hints=len(debug_hints),
        ctags_used=ctags_used,
        ctags_error=ctags_error,
    )


def open_index(db_path: Path | str) -> IndexDb:
    return IndexDb(db_path)


def ingest_compile_database(repo_root: Path | str, compile_commands: Path | str, db_path: Path | str) -> int:
    units = load_compile_database(compile_commands, repo_root)
    conn = open_database(db_path)
    try:
        replace_compile_units(conn, units)
    finally:
        conn.close()
    return len(units)


def clangd_check(source_file: Path | str, compile_commands_dir: Path | str, db_path: Path | str | None = None) -> int:
    diagnostics = run_clangd_check(source_file, compile_commands_dir)
    if db_path is not None:
        conn = open_database(db_path)
        try:
            replace_diagnostics(conn, diagnostics, source="clangd")
        finally:
            conn.close()
    return len(diagnostics)


def libclang_scan(repo_root: Path | str, compile_commands: Path | str, db_path: Path | str) -> int:
    units = load_compile_database(compile_commands, repo_root)
    diagnostics = run_libclang_scan(repo_root, compile_commands)
    conn = open_database(db_path)
    try:
        replace_compile_units(conn, units)
        replace_diagnostics(conn, diagnostics, source="libclang")
    finally:
        conn.close()
    return len(diagnostics)
