#ifndef EXPANSION_DMA_06_H
#define EXPANSION_DMA_06_H

#include "fw_types.h"

/* 繁體中文註解：dma 子系統第 06 階段，用來擴大假 firmware 架構並測試索引器壓力。 */
typedef struct fw_dma_06_state {
    uint32_t counter;
    uint32_t watermark;
    uint32_t last_event;
    fw_status_t last_status;
} fw_dma_06_state_t;

void fw_dma_06_init(fw_dma_06_state_t *state);
fw_status_t fw_dma_06_tick(fw_dma_06_state_t *state, uint32_t event_id);
uint32_t fw_dma_06_score(const fw_dma_06_state_t *state);

#endif
