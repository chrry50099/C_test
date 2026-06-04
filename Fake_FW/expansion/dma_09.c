#include "expansion/dma_09.h"

#define DMA_09_WATERMARK (170u)

void fw_dma_09_init(fw_dma_09_state_t *state)
{
    state->counter = 9u;
    state->watermark = DMA_09_WATERMARK;
    state->last_event = 0u;
    state->last_status = FW_OK;
}

fw_status_t fw_dma_09_tick(fw_dma_09_state_t *state, uint32_t event_id)
{
    /* 繁體中文註解：依據 CPU macro 展開不同路徑，模擬跨核心 firmware 行為差異。 */
    state->last_event = event_id;

#if FW_ENABLE_NVME_FRONTEND
    state->counter += (event_id + 10u);
#elif FW_ENABLE_GC_WORKER
    state->counter += ((event_id ^ 12u) & 0xFu);
#else
    state->counter += 1u;
#endif

    if (state->counter > state->watermark + FW_PAGE_SIZE) {
        state->last_status = FW_ERR_BUSY;
        return FW_ERR_BUSY;
    }

    state->last_status = FW_OK;
    return FW_OK;
}

uint32_t fw_dma_09_score(const fw_dma_09_state_t *state)
{
    return state->counter ^ state->watermark ^ state->last_event;
}
