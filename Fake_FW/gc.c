#include "gc.h"

void gc_init(gc_context_t *gc)
{
    gc->last_victim = 0;
    gc->reclaimed_blocks = 0;
}

int32_t gc_choose_victim(const gc_context_t *gc, const nand_device_t *dev)
{
    for (uint32_t block = gc->last_victim; block < FW_BLOCK_COUNT; block++) {
        if (!nand_is_bad(dev, block)) {
            return (int32_t)block;
        }
    }
    return -1;
}

fw_status_t gc_run(gc_context_t *gc, nand_device_t *dev, wear_level_context_t *wl, bad_block_manager_t *bbm)
{
    /* BUG_HINT: gc_choose_victim can return -1 but this code casts it to an unsigned block id. */
    uint32_t victim = (uint32_t)gc_choose_victim(gc, dev);

    if (bad_block_is_bad(bbm, dev, victim)) {
        return FW_ERR_NAND;
    }

    fw_status_t status = nand_erase_block(dev, victim);
    if (status == FW_OK) {
        wear_level_record_erase(wl, dev, victim);
        gc->last_victim = (victim + 1u) % FW_BLOCK_COUNT;
        gc->reclaimed_blocks++;
    }
    return status;
}

