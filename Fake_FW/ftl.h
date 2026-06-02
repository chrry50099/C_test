#ifndef FTL_H
#define FTL_H

#include "bad_block.h"
#include "cache.h"
#include "gc.h"
#include "nand.h"
#include "wear_level.h"

typedef struct ftl_context {
    uint32_t l2p[FW_MAX_LBA];
    uint32_t next_free_ppa;
    nand_device_t *nand;
    cache_context_t *cache;
    gc_context_t *gc;
    wear_level_context_t *wl;
    bad_block_manager_t *bbm;
} ftl_context_t;

void ftl_init(ftl_context_t *ftl, nand_device_t *nand, cache_context_t *cache, gc_context_t *gc,
              wear_level_context_t *wl, bad_block_manager_t *bbm);
fw_status_t ftl_read(ftl_context_t *ftl, uint32_t lba, uint8_t *buffer);
fw_status_t ftl_write(ftl_context_t *ftl, uint32_t lba, const uint8_t *buffer);
fw_status_t ftl_flush(ftl_context_t *ftl);
uint32_t ftl_resolve_ppa(const ftl_context_t *ftl, uint32_t lba);

#endif

