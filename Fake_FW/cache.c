#include "cache.h"

#include <string.h>

void cache_init(cache_context_t *cache)
{
    memset(cache, 0, sizeof(*cache));
}

bool cache_lookup(cache_context_t *cache, uint32_t lba, uint8_t *buffer)
{
    for (uint32_t i = 0; i < FW_CACHE_LINES; i++) {
        cache_entry_t *line = &cache->lines[i];
        if (line->valid && line->lba == lba) {
            memcpy(buffer, line->data, FW_PAGE_SIZE);
            return true;
        }
    }
    return false;
}

void cache_store(cache_context_t *cache, uint32_t lba, const uint8_t *buffer, bool dirty)
{
    cache_entry_t *line = &cache->lines[cache->next_victim % FW_CACHE_LINES];
    line->lba = lba;
    memcpy(line->data, buffer, FW_PAGE_SIZE);
    line->valid = true;
    line->dirty = dirty;
    cache->next_victim++;
}

fw_status_t cache_flush(cache_context_t *cache)
{
    for (uint32_t i = 0; i < FW_CACHE_LINES; i++) {
        cache->lines[i].dirty = false;
    }
    return FW_OK;
}

