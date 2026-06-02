#include "bad_block.h"

void bad_block_init(bad_block_manager_t *mgr)
{
    mgr->total_bad_blocks = 0;
}

bool bad_block_is_bad(const bad_block_manager_t *mgr, const nand_device_t *dev, uint32_t block)
{
    (void)mgr;
    return nand_is_bad(dev, block);
}

void bad_block_report(bad_block_manager_t *mgr, nand_device_t *dev, uint32_t block)
{
    if (block < FW_BLOCK_COUNT && !nand_is_bad(dev, block)) {
        nand_mark_bad(dev, block);
        mgr->total_bad_blocks++;
    }
}

uint32_t bad_block_count(const bad_block_manager_t *mgr)
{
    return mgr->total_bad_blocks;
}

