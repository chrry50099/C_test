#ifndef CACHE_H
#define CACHE_H

#include "fw_types.h"

typedef struct cache_entry {
    uint32_t lba;
    uint8_t data[FW_PAGE_SIZE];
    bool valid;
    bool dirty;
} cache_entry_t;

typedef struct cache_context {
    cache_entry_t lines[FW_CACHE_LINES];
    uint32_t next_victim;
} cache_context_t;

void cache_init(cache_context_t *cache);
bool cache_lookup(cache_context_t *cache, uint32_t lba, uint8_t *buffer);
void cache_store(cache_context_t *cache, uint32_t lba, const uint8_t *buffer, bool dirty);
fw_status_t cache_flush(cache_context_t *cache);

#endif

