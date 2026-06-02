from __future__ import annotations

import sqlite3
from pathlib import Path

from code_indexer.models import CallSite, DebugHint, FunctionDef, IdentifierRef, SourceFile, Symbol

SCHEMA = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS debug_hints;
DROP TABLE IF EXISTS identifiers;
DROP TABLE IF EXISTS calls;
DROP TABLE IF EXISTS symbols;
DROP TABLE IF EXISTS functions;
DROP TABLE IF EXISTS files;
DROP TABLE IF EXISTS modules;

CREATE TABLE modules (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    module_id INTEGER NOT NULL REFERENCES modules(id),
    sha256 TEXT NOT NULL,
    mtime REAL NOT NULL,
    size INTEGER NOT NULL
);

CREATE TABLE functions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    signature TEXT NOT NULL,
    file_id INTEGER NOT NULL REFERENCES files(id),
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    scope TEXT NOT NULL
);

CREATE TABLE calls (
    id INTEGER PRIMARY KEY,
    caller_function_id INTEGER REFERENCES functions(id),
    caller_name TEXT NOT NULL,
    callee_name TEXT NOT NULL,
    resolved_callee_id INTEGER REFERENCES functions(id),
    file_id INTEGER NOT NULL REFERENCES files(id),
    line INTEGER NOT NULL,
    column INTEGER NOT NULL
);

CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    file_id INTEGER REFERENCES files(id),
    line INTEGER,
    column INTEGER,
    signature TEXT,
    scope TEXT,
    source TEXT NOT NULL
);

CREATE TABLE identifiers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    file_id INTEGER NOT NULL REFERENCES files(id),
    function_id INTEGER REFERENCES functions(id),
    function_name TEXT,
    line INTEGER NOT NULL,
    column INTEGER NOT NULL
);

CREATE TABLE debug_hints (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id),
    line INTEGER NOT NULL,
    text TEXT NOT NULL
);

CREATE INDEX idx_functions_name ON functions(name);
CREATE INDEX idx_calls_callee ON calls(callee_name);
CREATE INDEX idx_calls_caller ON calls(caller_name);
CREATE INDEX idx_symbols_name ON symbols(name);
CREATE INDEX idx_identifiers_name ON identifiers(name);
"""


class IndexDb:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "IndexDb":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def summary(self) -> dict[str, int]:
        tables = ["files", "modules", "functions", "calls", "symbols", "identifiers", "debug_hints"]
        return {table: self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}

    def get_symbol(self, name: str) -> list[Symbol]:
        rows = self.conn.execute(
            """
            SELECT s.name, s.kind, f.path, s.line, s.column, s.signature, s.scope, s.source
            FROM symbols s
            LEFT JOIN files f ON f.id = s.file_id
            WHERE s.name = ?
            ORDER BY s.source, f.path, s.line
            """,
            (name,),
        ).fetchall()
        return [
            Symbol(
                name=row["name"],
                kind=row["kind"],
                path=row["path"] or "",
                line=row["line"],
                column=row["column"],
                signature=row["signature"],
                scope=row["scope"],
                source=row["source"],
            )
            for row in rows
        ]

    def get_callers(self, function_name: str) -> list[CallSite]:
        rows = self.conn.execute(
            """
            SELECT c.caller_name, c.callee_name, f.path, c.line, c.column, c.resolved_callee_id
            FROM calls c
            JOIN files f ON f.id = c.file_id
            WHERE c.callee_name = ?
            ORDER BY f.path, c.line
            """,
            (function_name,),
        ).fetchall()
        return [_call_site(row) for row in rows]

    def get_callees(self, function_name: str) -> list[CallSite]:
        rows = self.conn.execute(
            """
            SELECT c.caller_name, c.callee_name, f.path, c.line, c.column, c.resolved_callee_id
            FROM calls c
            JOIN files f ON f.id = c.file_id
            WHERE c.caller_name = ?
            ORDER BY f.path, c.line
            """,
            (function_name,),
        ).fetchall()
        return [_call_site(row) for row in rows]

    def get_debug_hints(self) -> list[DebugHint]:
        rows = self.conn.execute(
            """
            SELECT f.path, d.line, d.text
            FROM debug_hints d
            JOIN files f ON f.id = d.file_id
            ORDER BY f.path, d.line
            """
        ).fetchall()
        return [DebugHint(path=row["path"], line=row["line"], text=row["text"]) for row in rows]


def initialize_database(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def insert_index(
    conn: sqlite3.Connection,
    files: list[SourceFile],
    functions: list[FunctionDef],
    calls,
    identifiers: list[IdentifierRef],
    symbols: list[Symbol],
    debug_hints: list[DebugHint],
) -> None:
    module_ids: dict[str, int] = {}
    file_ids: dict[str, int] = {}
    function_ids: dict[tuple[str, str, int], int] = {}
    first_function_by_name: dict[str, int] = {}

    for file in files:
        module_id = module_ids.get(file.module)
        if module_id is None:
            cursor = conn.execute("INSERT INTO modules(name) VALUES (?)", (file.module,))
            module_id = cursor.lastrowid
            module_ids[file.module] = module_id

        cursor = conn.execute(
            "INSERT INTO files(path, module_id, sha256, mtime, size) VALUES (?, ?, ?, ?, ?)",
            (file.rel_path, module_id, file.sha256, file.mtime, file.size),
        )
        file_ids[file.rel_path] = cursor.lastrowid

    for fn in functions:
        cursor = conn.execute(
            """
            INSERT INTO functions(name, signature, file_id, start_line, end_line, scope)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (fn.name, fn.signature, file_ids[fn.rel_path], fn.start_line, fn.end_line, fn.scope),
        )
        fn_id = cursor.lastrowid
        function_ids[(fn.rel_path, fn.name, fn.start_line)] = fn_id
        first_function_by_name.setdefault(fn.name, fn_id)

    caller_by_file_name: dict[tuple[str, str], int] = {}
    for (rel_path, name, _line), fn_id in function_ids.items():
        caller_by_file_name[(rel_path, name)] = fn_id

    for call in calls:
        caller_id = caller_by_file_name.get((call.rel_path, call.caller_name))
        resolved_id = first_function_by_name.get(call.callee_name)
        conn.execute(
            """
            INSERT INTO calls(caller_function_id, caller_name, callee_name, resolved_callee_id, file_id, line, column)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (caller_id, call.caller_name, call.callee_name, resolved_id, file_ids[call.rel_path], call.line, call.column),
        )

    for symbol in symbols:
        conn.execute(
            """
            INSERT INTO symbols(name, kind, file_id, line, column, signature, scope, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol.name,
                symbol.kind,
                file_ids.get(symbol.path),
                symbol.line,
                symbol.column,
                symbol.signature,
                symbol.scope,
                symbol.source,
            ),
        )

    function_by_file_line: dict[tuple[str, str], int] = {}
    for (rel_path, name, _line), fn_id in function_ids.items():
        function_by_file_line[(rel_path, name)] = fn_id

    for identifier in identifiers:
        function_id = None
        if identifier.function_name is not None:
            function_id = function_by_file_line.get((identifier.rel_path, identifier.function_name))
        conn.execute(
            """
            INSERT INTO identifiers(name, file_id, function_id, function_name, line, column)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                identifier.name,
                file_ids[identifier.rel_path],
                function_id,
                identifier.function_name,
                identifier.line,
                identifier.column,
            ),
        )

    for hint in debug_hints:
        conn.execute(
            "INSERT INTO debug_hints(file_id, line, text) VALUES (?, ?, ?)",
            (file_ids[hint.path], hint.line, hint.text),
        )

    conn.commit()


def tree_sitter_function_symbols(functions: list[FunctionDef]) -> list[Symbol]:
    return [
        Symbol(
            name=fn.name,
            kind="function",
            path=fn.rel_path,
            line=fn.start_line,
            column=None,
            signature=fn.signature,
            scope=fn.scope,
            source="tree-sitter",
        )
        for fn in functions
    ]


def _call_site(row: sqlite3.Row) -> CallSite:
    return CallSite(
        caller_name=row["caller_name"],
        callee_name=row["callee_name"],
        path=row["path"],
        line=row["line"],
        column=row["column"],
        resolved=row["resolved_callee_id"] is not None,
    )

