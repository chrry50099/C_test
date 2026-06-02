#ifndef GC_H
#define GC_H

#include "bad_block.h"
#include "nand.h"
#include "wear_level.h"

typedef struct gc_context {
    uint32_t last_victim;
    uint32_t reclaimed_blocks;
} gc_context_t;

void gc_init(gc_context_t *gc);
int32_t gc_choose_victim(const gc_context_t *gc, const nand_device_t *dev);
fw_status_t gc_run(gc_context_t *gc, nand_device_t *dev, wear_level_context_t *wl, bad_block_manager_t *bbm);

#endif

