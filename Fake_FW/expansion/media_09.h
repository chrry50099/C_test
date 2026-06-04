#ifndef EXPANSION_MEDIA_09_H
#define EXPANSION_MEDIA_09_H

#include "fw_types.h"

/* 繁體中文註解：media 子系統第 09 階段，用來擴大假 firmware 架構並測試索引器壓力。 */
typedef struct fw_media_09_state {
    uint32_t counter;
    uint32_t watermark;
    uint32_t last_event;
    fw_status_t last_status;
} fw_media_09_state_t;

void fw_media_09_init(fw_media_09_state_t *state);
fw_status_t fw_media_09_tick(fw_media_09_state_t *state, uint32_t event_id);
uint32_t fw_media_09_score(const fw_media_09_state_t *state);

#endif
