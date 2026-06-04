#ifndef EXPANSION_IPC_05_H
#define EXPANSION_IPC_05_H

#include "fw_types.h"

/* 繁體中文註解：ipc 子系統第 05 階段，用來擴大假 firmware 架構並測試索引器壓力。 */
typedef struct fw_ipc_05_state {
    uint32_t counter;
    uint32_t watermark;
    uint32_t last_event;
    fw_status_t last_status;
} fw_ipc_05_state_t;

void fw_ipc_05_init(fw_ipc_05_state_t *state);
fw_status_t fw_ipc_05_tick(fw_ipc_05_state_t *state, uint32_t event_id);
uint32_t fw_ipc_05_score(const fw_ipc_05_state_t *state);

#endif
