#ifndef BAD_BLOCK_H
#define BAD_BLOCK_H

#include "nand.h"

typedef struct bad_block_manager {
    uint32_t total_bad_blocks;
} bad_block_manager_t;

void bad_block_init(bad_block_manager_t *mgr);
bool bad_block_is_bad(const bad_block_manager_t *mgr, const nand_device_t *dev, uint32_t block);
void bad_block_report(bad_block_manager_t *mgr, nand_device_t *dev, uint32_t block);
uint32_t bad_block_count(const bad_block_manager_t *mgr);

#endif

