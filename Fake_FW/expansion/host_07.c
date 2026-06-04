#include "expansion/host_07.h"
#include "expansion/host_08.h"

#define HOST_07_WATERMARK (136u)

void fw_host_07_init(fw_host_07_state_t *state)
{
    state->counter = 7u;
    state->watermark = HOST_07_WATERMARK;
    state->last_event = 0u;
    state->last_status = FW_OK;
}

fw_status_t fw_host_07_tick(fw_host_07_state_t *state, uint32_t event_id)
{
    /* 繁體中文註解：依據 CPU macro 展開不同路徑，模擬跨核心 firmware 行為差異。 */
    state->last_event = event_id;

#if FW_ENABLE_NVME_FRONTEND
    state->counter += (event_id + 8u);
#elif FW_ENABLE_GC_WORKER
    state->counter += ((event_id ^ 10u) & 0xFu);
#else
    state->counter += 1u;
#endif

    if ((event_id & 1u) == 0u) {
        fw_host_08_state_t next_state;
        fw_host_08_init(&next_state);
        state->watermark += fw_host_08_score(&next_state) & 0x3u;
    }

    if (state->counter > state->watermark + FW_PAGE_SIZE) {
        state->last_status = FW_ERR_BUSY;
        return FW_ERR_BUSY;
    }

    state->last_status = FW_OK;
    return FW_OK;
}

uint32_t fw_host_07_score(const fw_host_07_state_t *state)
{
    return state->counter ^ state->watermark ^ state->last_event;
}
