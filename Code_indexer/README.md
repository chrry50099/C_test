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

## Tests

```powershell
uv run pytest
```
