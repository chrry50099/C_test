#include "expansion/power_00.h"
#include "expansion/power_01.h"

#define POWER_00_WATERMARK (17u)

void fw_power_00_init(fw_power_00_state_t *state)
{
    state->counter = 0u;
    state->watermark = POWER_00_WATERMARK;
    state->last_event = 0u;
    state->last_status = FW_OK;
}

fw_status_t fw_power_00_tick(fw_power_00_state_t *state, uint32_t event_id)
{
    /* 繁體中文註解：依據 CPU macro 展開不同路徑，模擬跨核心 firmware 行為差異。 */
    state->last_event = event_id;

#if FW_ENABLE_NVME_FRONTEND
    state->counter += (event_id + 1u);
#elif FW_ENABLE_GC_WORKER
    state->counter += ((event_id ^ 3u) & 0xFu);
#else
    state->counter += 1u;
#endif

    if ((event_id & 1u) == 0u) {
        fw_power_01_state_t next_state;
        fw_power_01_init(&next_state);
        state->watermark += fw_power_01_score(&next_state) & 0x3u;
    }

    if (state->counter > state->watermark + FW_PAGE_SIZE) {
        state->last_status = FW_ERR_BUSY;
        return FW_ERR_BUSY;
    }

    state->last_status = FW_OK;
    return FW_OK;
}

uint32_t fw_power_00_score(const fw_power_00_state_t *state)
{
    return state->counter ^ state->watermark ^ state->last_event;
}
