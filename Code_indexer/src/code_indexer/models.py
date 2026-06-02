from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceFile:
    path: Path
    rel_path: str
    module: str
    sha256: str
    mtime: float
    size: int


@dataclass(frozen=True)
class FunctionDef:
    name: str
    signature: str
    rel_path: str
    start_line: int
    end_line: int
    scope: str


@dataclass(frozen=True)
class CallExpr:
    caller_name: str
    callee_name: str
    rel_path: str
    line: int
    column: int


@dataclass(frozen=True)
class IdentifierRef:
    name: str
    rel_path: str
    function_name: str | None
    line: int
    column: int


@dataclass(frozen=True)
class Symbol:
    name: str
    kind: str
    path: str
    line: int | None
    column: int | None
    signature: str | None
    scope: str | None
    source: str


@dataclass(frozen=True)
class CallSite:
    caller_name: str
    callee_name: str
    path: str
    line: int
    column: int
    resolved: bool


@dataclass(frozen=True)
class DebugHint:
    path: str
    line: int
    text: str


@dataclass(frozen=True)
class MacroConfig:
    profile: str
    name: str
    value: str | None


@dataclass(frozen=True)
class CompileUnit:
    rel_path: str
    directory: str
    command: str
    target: str
    profile: str
    defines: dict[str, str | None]
    include_paths: list[str]
    arguments: list[str]


@dataclass(frozen=True)
class Diagnostic:
    source: str
    rel_path: str
    line: int | None
    column: int | None
    severity: str
    message: str
    profile: str | None


@dataclass(frozen=True)
class ParsedFile:
    functions: list[FunctionDef]
    calls: list[CallExpr]
    identifiers: list[IdentifierRef]
    debug_hints: list[DebugHint]


@dataclass(frozen=True)
class IndexStats:
    files: int
    functions: int
    calls: int
    symbols: int
    identifiers: int
    debug_hints: int
    ctags_used: bool
    ctags_error: str | None = None
