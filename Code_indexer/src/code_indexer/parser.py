from __future__ import annotations

import re
from pathlib import Path

from tree_sitter import Language, Node, Parser
import tree_sitter_c

from code_indexer.models import CallExpr, DebugHint, FunctionDef, IdentifierRef, ParsedFile

BUG_HINT_RE = re.compile(r"BUG_HINT:\s*(?P<text>.+)")


class CParser:
    def __init__(self) -> None:
        language = Language(tree_sitter_c.language())
        self._parser = Parser()
        self._parser.language = language

    def parse_file(self, path: Path, rel_path: str) -> ParsedFile:
        source = path.read_bytes()
        tree = self._parser.parse(source)
        root = tree.root_node

        functions: list[FunctionDef] = []
        calls: list[CallExpr] = []
        identifiers: list[IdentifierRef] = []

        for node in _walk(root):
            if node.type == "function_definition":
                function = _function_def_from_node(node, source, rel_path)
                if function is not None:
                    functions.append(function)
                    calls.extend(_calls_in_function(node, source, rel_path, function.name))
                    identifiers.extend(_identifiers_in_function(node, source, rel_path, function.name))

        function_spans = {(fn.start_line, fn.end_line) for fn in functions}
        for node in _walk(root):
            if node.type == "identifier" and not _inside_any_span(node.start_point.row + 1, function_spans):
                identifiers.append(
                    IdentifierRef(
                        name=_node_text(node, source),
                        rel_path=rel_path,
                        function_name=None,
                        line=node.start_point.row + 1,
                        column=node.start_point.column + 1,
                    )
                )

        return ParsedFile(
            functions=functions,
            calls=calls,
            identifiers=identifiers,
            debug_hints=_debug_hints(source, rel_path),
        )


def _function_def_from_node(node: Node, source: bytes, rel_path: str) -> FunctionDef | None:
    declarator = _first_child_of_type(node, "function_declarator")
    if declarator is None:
        return None

    identifier = _first_child_of_type(declarator, "identifier")
    if identifier is None:
        return None

    body = _first_child_of_type(node, "compound_statement")
    signature_end = body.start_byte if body is not None else declarator.end_byte
    signature = " ".join(source[node.start_byte:signature_end].decode("utf-8", errors="replace").split())

    return FunctionDef(
        name=_node_text(identifier, source),
        signature=signature,
        rel_path=rel_path,
        start_line=node.start_point.row + 1,
        end_line=node.end_point.row + 1,
        scope="global",
    )


def _calls_in_function(node: Node, source: bytes, rel_path: str, caller_name: str) -> list[CallExpr]:
    calls: list[CallExpr] = []
    for child in _walk(node):
        if child.type != "call_expression":
            continue
        callee_node = child.child_by_field_name("function")
        if callee_node is None:
            continue
        callee_name = _callable_name(callee_node, source)
        if callee_name:
            calls.append(
                CallExpr(
                    caller_name=caller_name,
                    callee_name=callee_name,
                    rel_path=rel_path,
                    line=child.start_point.row + 1,
                    column=child.start_point.column + 1,
                )
            )
    return calls


def _identifiers_in_function(node: Node, source: bytes, rel_path: str, function_name: str) -> list[IdentifierRef]:
    identifiers: list[IdentifierRef] = []
    for child in _walk(node):
        if child.type == "identifier":
            identifiers.append(
                IdentifierRef(
                    name=_node_text(child, source),
                    rel_path=rel_path,
                    function_name=function_name,
                    line=child.start_point.row + 1,
                    column=child.start_point.column + 1,
                )
            )
    return identifiers


def _callable_name(node: Node, source: bytes) -> str | None:
    if node.type == "identifier":
        return _node_text(node, source)
    if node.type in {"field_expression", "pointer_expression", "parenthesized_expression"}:
        text = _node_text(node, source)
        return text.replace("\n", " ").strip()
    nested = _first_child_of_type(node, "identifier")
    if nested is not None:
        return _node_text(nested, source)
    return None


def _debug_hints(source: bytes, rel_path: str) -> list[DebugHint]:
    hints: list[DebugHint] = []
    for idx, line in enumerate(source.decode("utf-8", errors="replace").splitlines(), start=1):
        match = BUG_HINT_RE.search(line)
        if match:
            hints.append(DebugHint(path=rel_path, line=idx, text=_clean_hint_text(match.group("text"))))
    return hints


def _clean_hint_text(text: str) -> str:
    return text.strip().removesuffix("*/").strip()


def _walk(node: Node):
    yield node
    for child in node.children:
        yield from _walk(child)


def _first_child_of_type(node: Node, node_type: str) -> Node | None:
    for child in _walk(node):
        if child.type == node_type:
            return child
    return None


def _node_text(node: Node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _inside_any_span(line: int, spans: set[tuple[int, int]]) -> bool:
    return any(start <= line <= end for start, end in spans)
