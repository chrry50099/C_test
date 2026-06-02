# Code Indexer

Small C source indexer for agent/debug experiments. It scans `.c` and `.h`
files, extracts syntax facts with tree-sitter, enriches symbol coverage with
Universal Ctags, and stores the result in SQLite.

## Setup

Python dependencies are managed by `uv`:

```powershell
cd D:\Work_D\C_test\Code_indexer
uv sync
```

The Python side of libclang is installed by `uv` through the `libclang`
dependency in `pyproject.toml`.

Universal Ctags is optional for smoke tests but required for full macro,
struct, enum, typedef, and prototype coverage:

```powershell
winget install --id UniversalCtags.Ctags -e
```

If `ctags` is installed but not visible in the current terminal PATH, add the
winget-installed directory to the user PATH:

```powershell
$ctags = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter ctags.exe -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match "UniversalCtags" } |
    Select-Object -First 1

$ctagsDir = Split-Path -Parent $ctags.FullName
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$ctagsDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$ctagsDir", "User")
}

# Also update the current PowerShell session so ctags works immediately.
if ($env:Path -notlike "*$ctagsDir*") {
    $env:Path = "$env:Path;$ctagsDir"
}

ctags --version
```

Future PowerShell windows will inherit the user PATH. Verify with:

```powershell
ctags --version
uv run code-index scan ..\Fake_FW --db .\index.sqlite
```

Alternatively, pass the executable explicitly without changing PATH:

```powershell
$ctags = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter ctags.exe -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match "UniversalCtags" } |
    Select-Object -First 1 -ExpandProperty FullName

uv run code-index scan ..\Fake_FW --db .\index.sqlite --ctags $ctags
```

To compile `Fake_FW`, install CMake and a C compiler if they are not already in
`PATH`:

```powershell
winget install --id Kitware.CMake -e
winget install --id LLVM.LLVM -e
```

After installing LLVM, open a new PowerShell and verify:

```powershell
clang --version
clangd --version
```

## Fake Firmware Variants

`Fake_FW/conf.h` defines CPU-specific macro switches:

```c
#define FW_CPU0 0
#define FW_CPU1 1

#ifndef FW_CPU_ID
#define FW_CPU_ID FW_CPU0
#endif
```

`Fake_FW/CMakeLists.txt` builds two targets:

```text
fake_ssd_fw_cpu0 -> -DFW_CPU_ID=0
fake_ssd_fw_cpu1 -> -DFW_CPU_ID=1
```

Generate a compile database for clangd/libclang:

```powershell
cmake -S ..\Fake_FW -B ..\Fake_FW\build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build ..\Fake_FW\build
```

## CLI

```powershell
uv run code-index scan ..\Fake_FW --db .\index.sqlite
uv run code-index summary --db .\index.sqlite
uv run code-index symbol ftl_write --db .\index.sqlite
uv run code-index callers nand_program_page --db .\index.sqlite
uv run code-index callees nvme_submit_write --db .\index.sqlite
uv run code-index debug-hints --db .\index.sqlite
```

`scan` continues when `ctags` is missing and records tree-sitter function
symbols. Use `--require-ctags` if a missing ctags executable should fail the
scan.

Additional clang-oriented commands:

```powershell
uv run code-index doctor ..\Fake_FW --compile-commands ..\Fake_FW\build\compile_commands.json
uv run code-index compile-db ..\Fake_FW --compile-commands ..\Fake_FW\build\compile_commands.json --db .\index.sqlite
uv run code-index variants --db .\index.sqlite
uv run code-index clangd-check ..\Fake_FW\ftl.c --compile-commands ..\Fake_FW\build --db .\index.sqlite
uv run code-index libclang-scan ..\Fake_FW --compile-commands ..\Fake_FW\build\compile_commands.json --db .\index.sqlite
uv run code-index diagnostics --db .\index.sqlite
```

Tool roles:

- tree-sitter: fast syntax parsing for functions, call expressions, and identifiers.
- Universal Ctags: fast symbol inventory for functions, macros, structs, enums, typedefs, and prototypes.
- clangd: compiler-aware diagnostics and IDE-style checks using `compile_commands.json`.
- libclang: Python-accessible semantic diagnostics using the same per-target compile arguments.

`libclang-scan` needs enough compiler context to find standard C headers such
as `stdbool.h`. If diagnostics report missing standard headers, install LLVM and
generate a real CMake `compile_commands.json` before rerunning the scan.

## Tests

```powershell
uv run pytest
```
