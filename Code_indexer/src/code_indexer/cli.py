from __future__ import annotations

import argparse
from pathlib import Path

from code_indexer.api import build_index, open_index
from code_indexer.ctags import CtagsUnavailable


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        return _scan(args)
    if args.command == "summary":
        return _summary(args)
    if args.command == "symbol":
        return _symbol(args)
    if args.command == "callers":
        return _callers(args)
    if args.command == "callees":
        return _callees(args)
    if args.command == "debug-hints":
        return _debug_hints(args)

    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="code-index", description="Index C source code for agent debugging.")
    subparsers = parser.add_subparsers(dest="command")

    scan = subparsers.add_parser("scan", help="Scan a C repo and build a SQLite index.")
    scan.add_argument("repo", type=Path)
    scan.add_argument("--db", type=Path, required=True)
    scan.add_argument("--require-ctags", action="store_true", help="Fail if Universal Ctags is not available.")
    scan.add_argument("--ctags", default="ctags", help="ctags executable name or path.")

    for name in ("summary", "debug-hints"):
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


if __name__ == "__main__":
    raise SystemExit(main())

