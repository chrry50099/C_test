from __future__ import annotations

import argparse
from pathlib import Path
import time

from code_indexer.api import build_index, open_index
from code_indexer.clang_tools import run_clangd_check, run_libclang_scan
from code_indexer.compile_db import load_compile_database
from code_indexer.ctags import CtagsUnavailable
from code_indexer.db import open_database, replace_compile_units, replace_diagnostics
from code_indexer.toolchain import run_doctor

TIMED_COMMANDS = {"scan", "compile-db", "doctor", "clangd-check", "libclang-scan"}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "scan": _scan,
        "summary": _summary,
        "symbol": _symbol,
        "callers": _callers,
        "callees": _callees,
        "debug-hints": _debug_hints,
        "compile-db": _compile_db,
        "variants": _variants,
        "diagnostics": _diagnostics,
        "doctor": _doctor,
        "clangd-check": _clangd_check,
        "libclang-scan": _libclang_scan,
    }
    handler = handlers.get(args.command)
    if handler is not None:
        if args.command in TIMED_COMMANDS:
            return _run_timed(args.command, handler, args)
        return handler(args)

    parser.print_help()
    return 1


def _run_timed(command: str, handler, args: argparse.Namespace) -> int:
    started = time.perf_counter()
    try:
        return handler(args)
    finally:
        elapsed = time.perf_counter() - started
        print(f"elapsed command={command} seconds={elapsed:.3f}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="code-index", description="Index C source code for agent debugging.")
    subparsers = parser.add_subparsers(dest="command")

    scan = subparsers.add_parser("scan", help="Scan a C repo and build a SQLite index.")
    scan.add_argument("repo", type=Path)
    scan.add_argument("--db", type=Path, required=True)
    scan.add_argument("--require-ctags", action="store_true", help="Fail if Universal Ctags is not available.")
    scan.add_argument("--ctags", default="ctags", help="ctags executable name or path.")

    compile_db = subparsers.add_parser("compile-db", help="Ingest compile_commands.json into the SQLite index.")
    compile_db.add_argument("repo", type=Path)
    compile_db.add_argument("--compile-commands", type=Path, required=True)
    compile_db.add_argument("--db", type=Path, required=True)

    doctor = subparsers.add_parser("doctor", help="Check external C analysis toolchain availability.")
    doctor.add_argument("repo", type=Path, nargs="?")
    doctor.add_argument("--compile-commands", type=Path)

    clangd = subparsers.add_parser("clangd-check", help="Run clangd --check for one source file.")
    clangd.add_argument("source", type=Path)
    clangd.add_argument("--compile-commands", type=Path, required=True, help="Build directory containing compile_commands.json.")
    clangd.add_argument("--db", type=Path)

    libclang = subparsers.add_parser("libclang-scan", help="Run libclang diagnostics using compile_commands.json.")
    libclang.add_argument("repo", type=Path)
    libclang.add_argument("--compile-commands", type=Path, required=True)
    libclang.add_argument("--db", type=Path, required=True)

    for name in ("summary", "debug-hints", "variants", "diagnostics"):
        command = subparsers.add_parser(name)
        command.add_argument("--db", type=Path, required=True)

    symbol = subparsers.add_parser("symbol", help="Find symbols by exact name.")
    symbol.add_argument("name")
    symbol.add_argument("--db", type=Path, required=True)

    callers = subparsers.add_parser("callers", help="Find call sites that call a function.")
    callers.add_argument("name")
    callers.add_argument("--db", type=Path, required=True)

    callees = subparsers.add_parser("callees", help="Find calls made by a function.")
    callees.add_argument("name")
    callees.add_argument("--db", type=Path, required=True)

    return parser


def _scan(args: argparse.Namespace) -> int:
    try:
        stats = build_index(args.repo, args.db, require_ctags=args.require_ctags, ctags_executable=args.ctags)
    except CtagsUnavailable as exc:
        print(f"ctags error: {exc}")
        return 2

    print(
        "indexed "
        f"files={stats.files} functions={stats.functions} calls={stats.calls} "
        f"symbols={stats.symbols} identifiers={stats.identifiers} debug_hints={stats.debug_hints}"
    )
    if stats.ctags_used:
        print("ctags=used")
    else:
        print(f"ctags=not-used reason={stats.ctags_error}")
    return 0


def _summary(args: argparse.Namespace) -> int:
    with open_index(args.db) as db:
        for name, count in db.summary().items():
            print(f"{name}: {count}")
    return 0


def _symbol(args: argparse.Namespace) -> int:
    with open_index(args.db) as db:
        for symbol in db.get_symbol(args.name):
            line = symbol.line if symbol.line is not None else "?"
            print(f"{symbol.kind} {symbol.name} {symbol.path}:{line} source={symbol.source}")
    return 0


def _callers(args: argparse.Namespace) -> int:
    with open_index(args.db) as db:
        for call in db.get_callers(args.name):
            resolved = "resolved" if call.resolved else "unresolved"
            print(f"{call.caller_name} -> {call.callee_name} {call.path}:{call.line}:{call.column} {resolved}")
    return 0


def _callees(args: argparse.Namespace) -> int:
    with open_index(args.db) as db:
        for call in db.get_callees(args.name):
            resolved = "resolved" if call.resolved else "unresolved"
            print(f"{call.caller_name} -> {call.callee_name} {call.path}:{call.line}:{call.column} {resolved}")
    return 0


def _debug_hints(args: argparse.Namespace) -> int:
    with open_index(args.db) as db:
        for hint in db.get_debug_hints():
            print(f"{hint.path}:{hint.line}: {hint.text}")
    return 0


def _compile_db(args: argparse.Namespace) -> int:
    units = load_compile_database(args.compile_commands, args.repo)
    conn = open_database(args.db)
    try:
        replace_compile_units(conn, units)
    finally:
        conn.close()

    profiles = sorted({unit.profile for unit in units})
    print(f"compile_units={len(units)} profiles={','.join(profiles)}")
    return 0


def _variants(args: argparse.Namespace) -> int:
    with open_index(args.db) as db:
        for macro in db.get_variants():
            value = "" if macro.value is None else f"={macro.value}"
            print(f"{macro.profile}: {macro.name}{value}")
    return 0


def _diagnostics(args: argparse.Namespace) -> int:
    with open_index(args.db) as db:
        for diagnostic in db.get_diagnostics():
            line = diagnostic.line if diagnostic.line is not None else "?"
            column = diagnostic.column if diagnostic.column is not None else "?"
            profile = diagnostic.profile or "default"
            print(
                f"{diagnostic.source} {profile} {diagnostic.severity} "
                f"{diagnostic.rel_path}:{line}:{column}: {diagnostic.message}"
            )
    return 0


def _doctor(args: argparse.Namespace) -> int:
    statuses = run_doctor(args.repo, args.compile_commands)
    for status in statuses:
        state = "ok" if status.ok else "missing"
        print(f"{status.name}: {state} - {status.detail}")
    return 0 if all(status.ok for status in statuses if status.name != "compile_commands") else 1


def _clangd_check(args: argparse.Namespace) -> int:
    diagnostics = run_clangd_check(args.source, args.compile_commands)
    if args.db is not None:
        conn = open_database(args.db)
        try:
            replace_diagnostics(conn, diagnostics, source="clangd")
        finally:
            conn.close()
    for diagnostic in diagnostics:
        print(f"{diagnostic.severity}: {diagnostic.message}")
    print(f"clangd_diagnostics={len(diagnostics)}")
    return 0


def _libclang_scan(args: argparse.Namespace) -> int:
    units = load_compile_database(args.compile_commands, args.repo)
    diagnostics = run_libclang_scan(args.repo, args.compile_commands)
    conn = open_database(args.db)
    try:
        replace_compile_units(conn, units)
        replace_diagnostics(conn, diagnostics, source="libclang")
    finally:
        conn.close()
    print(f"compile_units={len(units)} libclang_diagnostics={len(diagnostics)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
