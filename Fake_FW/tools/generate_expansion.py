from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPANSION = ROOT / "expansion"

SUBSYSTEMS = [
    "host",
    "dma",
    "media",
    "ecc",
    "power",
    "thermal",
    "telemetry",
    "ipc",
    "qos",
]
MODULES_PER_SUBSYSTEM = 10


def guard_for(name: str) -> str:
    return f"EXPANSION_{name.upper()}_H"


def function_prefix(subsystem: str, index: int) -> str:
    return f"fw_{subsystem}_{index:02d}"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def header_text(subsystem: str, index: int) -> str:
    prefix = function_prefix(subsystem, index)
    type_name = f"{prefix}_state_t"
    guard = guard_for(f"{subsystem}_{index:02d}")
    title = f"{subsystem} 子系統第 {index:02d} 階段"
    return f"""#ifndef {guard}
#define {guard}

#include "fw_types.h"

/* 繁體中文註解：{title}，用來擴大假 firmware 架構並測試索引器壓力。 */
typedef struct {prefix}_state {{
    uint32_t counter;
    uint32_t watermark;
    uint32_t last_event;
    fw_status_t last_status;
}} {type_name};

void {prefix}_init({type_name} *state);
fw_status_t {prefix}_tick({type_name} *state, uint32_t event_id);
uint32_t {prefix}_score(const {type_name} *state);

#endif
"""


def source_text(subsystem: str, index: int) -> str:
    prefix = function_prefix(subsystem, index)
    next_include = ""
    next_calls = ""
    if index + 1 < MODULES_PER_SUBSYSTEM:
        next_prefix = function_prefix(subsystem, index + 1)
        next_include = f'#include "expansion/{subsystem}_{index + 1:02d}.h"\n'
        next_calls = f"""
    if ((event_id & 1u) == 0u) {{
        {next_prefix}_state_t next_state;
        {next_prefix}_init(&next_state);
        state->watermark += {next_prefix}_score(&next_state) & 0x3u;
    }}
"""

    cpu_path = f"""
#if FW_ENABLE_NVME_FRONTEND
    state->counter += (event_id + {index + 1}u);
#elif FW_ENABLE_GC_WORKER
    state->counter += ((event_id ^ {index + 3}u) & 0xFu);
#else
    state->counter += 1u;
#endif
"""

    return f"""#include "expansion/{subsystem}_{index:02d}.h"
{next_include}
#define {subsystem.upper()}_{index:02d}_WATERMARK ({(index + 1) * 17}u)

void {prefix}_init({prefix}_state_t *state)
{{
    state->counter = {index}u;
    state->watermark = {subsystem.upper()}_{index:02d}_WATERMARK;
    state->last_event = 0u;
    state->last_status = FW_OK;
}}

fw_status_t {prefix}_tick({prefix}_state_t *state, uint32_t event_id)
{{
    /* 繁體中文註解：依據 CPU macro 展開不同路徑，模擬跨核心 firmware 行為差異。 */
    state->last_event = event_id;
{cpu_path}{next_calls}
    if (state->counter > state->watermark + FW_PAGE_SIZE) {{
        state->last_status = FW_ERR_BUSY;
        return FW_ERR_BUSY;
    }}

    state->last_status = FW_OK;
    return FW_OK;
}}

uint32_t {prefix}_score(const {prefix}_state_t *state)
{{
    return state->counter ^ state->watermark ^ state->last_event;
}}
"""


def registry_header_text() -> str:
    return """#ifndef FW_EXT_REGISTRY_H
#define FW_EXT_REGISTRY_H

#include "fw_types.h"

typedef struct fw_ext_registry {
    uint32_t boot_count;
    uint32_t poll_count;
    fw_status_t last_status;
} fw_ext_registry_t;

void fw_ext_registry_bootstrap(fw_ext_registry_t *registry);
fw_status_t fw_ext_registry_poll(fw_ext_registry_t *registry, uint32_t event_id);

#endif
"""


def registry_source_text() -> str:
    includes = "\n".join(f'#include "expansion/{subsystem}_00.h"' for subsystem in SUBSYSTEMS)
    calls = []
    for subsystem in SUBSYSTEMS:
        prefix = function_prefix(subsystem, 0)
        calls.append(
            f"""    {prefix}_state_t {subsystem}_state;
    {prefix}_init(&{subsystem}_state);
    status = {prefix}_tick(&{subsystem}_state, event_id);
    registry->poll_count += {prefix}_score(&{subsystem}_state) & 0x7u;
    if (status != FW_OK) {{
        registry->last_status = status;
        return status;
    }}
"""
        )

    return f"""#include "fw_ext_registry.h"

{includes}

void fw_ext_registry_bootstrap(fw_ext_registry_t *registry)
{{
    /* 繁體中文註解：集中啟動擴充模組，方便產生更大的 call graph。 */
    registry->boot_count++;
    registry->poll_count = 0u;
    registry->last_status = FW_OK;
}}

fw_status_t fw_ext_registry_poll(fw_ext_registry_t *registry, uint32_t event_id)
{{
    fw_status_t status = FW_OK;

{''.join(calls)}    registry->last_status = FW_OK;
    return FW_OK;
}}
"""


def main() -> None:
    for subsystem in SUBSYSTEMS:
        for index in range(MODULES_PER_SUBSYSTEM):
            write_text(EXPANSION / f"{subsystem}_{index:02d}.h", header_text(subsystem, index))
            write_text(EXPANSION / f"{subsystem}_{index:02d}.c", source_text(subsystem, index))

    write_text(ROOT / "fw_ext_registry.h", registry_header_text())
    write_text(ROOT / "fw_ext_registry.c", registry_source_text())


if __name__ == "__main__":
    main()

