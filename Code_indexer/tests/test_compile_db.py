from pathlib import Path

from code_indexer.compile_db import clang_args_for_unit, load_compile_database


def test_load_compile_database_extracts_cpu_profiles(tmp_path: Path) -> None:
    repo = tmp_path / "Fake_FW"
    repo.mkdir()
    (repo / "ftl.c").write_text("int ftl(void) { return 0; }\n", encoding="utf-8")
    compile_commands = repo / "build" / "compile_commands.json"
    compile_commands.parent.mkdir()
    compile_commands.write_text(
        """
[
  {
    "directory": "%DIR%",
    "file": "%FILE%",
    "arguments": [
      "clang",
      "-std=c11",
      "-DFW_CPU_ID=0",
      "-I%INC%",
      "-c",
      "%FILE%",
      "-o",
      "CMakeFiles/fake_ssd_fw_cpu0.dir/ftl.c.obj"
    ]
  },
  {
    "directory": "%DIR%",
    "file": "%FILE%",
    "arguments": [
      "clang",
      "-std=c11",
      "-DFW_CPU_ID=1",
      "-I",
      "%INC%",
      "-c",
      "%FILE%",
      "-o",
      "CMakeFiles/fake_ssd_fw_cpu1.dir/ftl.c.obj"
    ]
  }
]
""".replace("%DIR%", repo.as_posix())
        .replace("%FILE%", (repo / "ftl.c").as_posix())
        .replace("%INC%", repo.as_posix()),
        encoding="utf-8",
    )

    units = load_compile_database(compile_commands, repo)

    assert [unit.profile for unit in units] == ["cpu0", "cpu1"]
    assert units[0].target == "fake_ssd_fw_cpu0"
    assert units[1].target == "fake_ssd_fw_cpu1"
    assert units[0].defines["FW_CPU_ID"] == "0"
    assert repo.as_posix() in units[1].include_paths
    assert "-DFW_CPU_ID=0" in clang_args_for_unit(units[0])

