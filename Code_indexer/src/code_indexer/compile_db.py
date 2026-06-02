from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

from code_indexer.models import CompileUnit

TARGET_RE = re.compile(r"CMakeFiles[\\/](?P<target>[^\\/]+)\.dir")


def load_compile_database(compile_commands: Path | str, repo_root: Path | str | None = None) -> list[CompileUnit]:
    compile_commands_path = Path(compile_commands).resolve()
    root = Path(repo_root).resolve() if repo_root is not None else compile_commands_path.parent
    entries = json.loads(compile_commands_path.read_text(encoding="utf-8"))
    units: list[CompileUnit] = []

    for entry in entries:
        directory = Path(entry.get("directory", compile_commands_path.parent)).resolve()
        file_path = Path(entry["file"])
        if not file_path.is_absolute():
            file_path = (directory / file_path).resolve()

        arguments = _entry_arguments(entry)
        defines = _extract_defines(arguments)
        include_paths = _extract_include_paths(arguments)
        command = entry.get("command") or " ".join(arguments)
        target = _infer_target(command, arguments)
        profile = _infer_profile(defines, target)

        units.append(
            CompileUnit(
                rel_path=_relative_or_absolute(file_path, root),
                directory=str(directory),
                command=command,
                target=target,
                profile=profile,
                defines=defines,
                include_paths=include_paths,
                arguments=arguments,
            )
        )

    return units


def clang_args_for_unit(unit: CompileUnit) -> list[str]:
    args: list[str] = []
    for name, value in unit.defines.items():
        if value is None:
            args.append(f"-D{name}")
        else:
            args.append(f"-D{name}={value}")
    for include_path in unit.include_paths:
        args.append(f"-I{include_path}")
    for arg in unit.arguments:
        if arg.startswith("-std="):
            args.append(arg)
    return args


def _entry_arguments(entry: dict) -> list[str]:
    arguments = entry.get("arguments")
    if isinstance(arguments, list):
        return [str(arg) for arg in arguments]
    command = entry.get("command", "")
    return shlex.split(command, posix=False)


def _extract_defines(arguments: list[str]) -> dict[str, str | None]:
    defines: dict[str, str | None] = {}
    iterator = iter(range(len(arguments)))
    for idx in iterator:
        arg = arguments[idx]
        value: str | None = None
        if arg in {"-D", "/D"} and idx + 1 < len(arguments):
            macro = arguments[idx + 1]
        elif arg.startswith("-D") and len(arg) > 2:
            macro = arg[2:]
        elif arg.startswith("/D") and len(arg) > 2:
            macro = arg[2:]
        else:
            continue

        macro = macro.strip('"')
        if "=" in macro:
            name, value = macro.split("=", 1)
        else:
            name = macro
        if name:
            defines[name] = value
    return defines


def _extract_include_paths(arguments: list[str]) -> list[str]:
    include_paths: list[str] = []
    for idx, arg in enumerate(arguments):
        if arg in {"-I", "/I"} and idx + 1 < len(arguments):
            include_paths.append(arguments[idx + 1].strip('"'))
        elif arg.startswith("-I") and len(arg) > 2:
            include_paths.append(arg[2:].strip('"'))
        elif arg.startswith("/I") and len(arg) > 2:
            include_paths.append(arg[2:].strip('"'))
    return include_paths


def _infer_target(command: str, arguments: list[str]) -> str:
    haystack = command + " " + " ".join(arguments)
    match = TARGET_RE.search(haystack)
    if match:
        return match.group("target")
    return "unknown"


def _infer_profile(defines: dict[str, str | None], target: str) -> str:
    cpu_id = defines.get("FW_CPU_ID")
    if cpu_id == "0":
        return "cpu0"
    if cpu_id == "1":
        return "cpu1"
    if "cpu0" in target.lower():
        return "cpu0"
    if "cpu1" in target.lower():
        return "cpu1"
    return "default"


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()

