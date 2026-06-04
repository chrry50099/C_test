#ifndef EXPANSION_TELEMETRY_07_H
#define EXPANSION_TELEMETRY_07_H

#include "fw_types.h"

/* 繁體中文註解：telemetry 子系統第 07 階段，用來擴大假 firmware 架構並測試索引器壓力。 */
typedef struct fw_telemetry_07_state {
    uint32_t counter;
    uint32_t watermark;
    uint32_t last_event;
    fw_status_t last_status;
} fw_telemetry_07_state_t;

void fw_telemetry_07_init(fw_telemetry_07_state_t *state);
fw_status_t fw_telemetry_07_tick(fw_telemetry_07_state_t *state, uint32_t event_id);
uint32_t fw_telemetry_07_score(const fw_telemetry_07_state_t *state);

#endif
