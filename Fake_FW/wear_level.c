#include "wear_level.h"

void wear_level_init(wear_level_context_t *wl)
{
#if FW_ENABLE_GC_WORKER
    wl->high_watermark = 40;
    wl->low_watermark = 4;
#else
    wl->high_watermark = 80;
    wl->low_watermark = 8;
#endif
}

void wear_level_record_erase(wear_level_context_t *wl, nand_device_t *dev, uint32_t block)
{
    (void)wl;
    if (block < FW_BLOCK_COUNT) {
        /* BUG_HINT: wear count is incremented without saturation handling. */
        dev->erase_count[block]++;
    }
}

uint32_t wear_level_select_cold_block(const wear_level_context_t *wl, const nand_device_t *dev)
{
    uint32_t best_block = 0;
    uint16_t best_count = UINT16_MAX;

    for (uint32_t block = 0; block < FW_BLOCK_COUNT; block++) {
        if (!nand_is_bad(dev, block) && dev->erase_count[block] < best_count) {
            best_block = block;
            best_count = dev->erase_count[block];
        }
    }

    if (best_count > wl->low_watermark) {
        return best_block;
    }
    return 0;
}

bool wear_level_needs_rotation(const wear_level_context_t *wl, const nand_device_t *dev)
{
    for (uint32_t block = 0; block < FW_BLOCK_COUNT; block++) {
        if (dev->erase_count[block] > wl->high_watermark) {
            return true;
        }
    }
    return false;
}
