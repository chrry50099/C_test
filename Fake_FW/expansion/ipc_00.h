#ifndef EXPANSION_IPC_00_H
#define EXPANSION_IPC_00_H

#include "fw_types.h"

/* 繁體中文註解：ipc 子系統第 00 階段，用來擴大假 firmware 架構並測試索引器壓力。 */
typedef struct fw_ipc_00_state {
    uint32_t counter;
    uint32_t watermark;
    uint32_t last_event;
    fw_status_t last_status;
} fw_ipc_00_state_t;

void fw_ipc_00_init(fw_ipc_00_state_t *state);
fw_status_t fw_ipc_00_tick(fw_ipc_00_state_t *state, uint32_t event_id);
uint32_t fw_ipc_00_score(const fw_ipc_00_state_t *state);

#endif
