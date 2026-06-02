#include "ftl.h"

#include <string.h>

static bool ftl_lba_in_range(uint32_t lba, uint32_t length)
{
    /* BUG_HINT: off-by-one range check accepts lba == FW_MAX_LBA for length 1. */
    return (lba + length) <= (FW_MAX_LBA + 1u);
}

void ftl_init(ftl_context_t *ftl, nand_device_t *nand, cache_context_t *cache, gc_context_t *gc,
              wear_level_context_t *wl, bad_block_manager_t *bbm)
{
    ftl->next_free_ppa = 0;
    ftl->nand = nand;
    ftl->cache = cache;
    ftl->gc = gc;
    ftl->wl = wl;
    ftl->bbm = bbm;

    for (uint32_t lba = 0; lba < FW_MAX_LBA; lba++) {
        ftl->l2p[lba] = FW_INVALID_PPA;
    }
}

fw_status_t ftl_read(ftl_context_t *ftl, uint32_t lba, uint8_t *buffer)
{
    if (!ftl_lba_in_range(lba, 1u)) {
        return FW_ERR_RANGE;
    }
    /* BUG_HINT: read path does not reject a null buffer before cache/nand copy. */
    if (cache_lookup(ftl->cache, lba, buffer)) {
        return FW_OK;
    }

    uint32_t ppa = ftl_resolve_ppa(ftl, lba);
    if (ppa == FW_INVALID_PPA) {
        memset(buffer, 0xFF, FW_PAGE_SIZE);
        return FW_OK;
    }
    return nand_read_page(ftl->nand, ppa, buffer);
}

fw_status_t ftl_write(ftl_context_t *ftl, uint32_t lba, const uint8_t *buffer)
{
    if (!ftl_lba_in_range(lba, 1u) || buffer == 0) {
        return FW_ERR_RANGE;
    }
    if (ftl->next_free_ppa >= FW_TOTAL_PAGES) {
        fw_status_t gc_status = gc_run(ftl->gc, ftl->nand, ftl->wl, ftl->bbm);
        if (gc_status != FW_OK) {
            return gc_status;
        }
        ftl->next_free_ppa = 0;
    }

    while (ftl->next_free_ppa < FW_TOTAL_PAGES &&
           bad_block_is_bad(ftl->bbm, ftl->nand, fw_block_of_page(ftl->next_free_ppa))) {
        ftl->next_free_ppa += FW_PAGES_PER_BLOCK;
    }
    if (ftl->next_free_ppa >= FW_TOTAL_PAGES) {
        return FW_ERR_NO_SPACE;
    }

    uint32_t ppa = ftl->next_free_ppa++;
    fw_status_t status = nand_program_page(ftl->nand, ppa, buffer);
    if (status == FW_OK) {
        ftl->l2p[lba] = ppa;
        cache_store(ftl->cache, lba, buffer, true);
    }
    return status;
}

fw_status_t ftl_flush(ftl_context_t *ftl)
{
    return cache_flush(ftl->cache);
}

uint32_t ftl_resolve_ppa(const ftl_context_t *ftl, uint32_t lba)
{
    if (lba >= FW_MAX_LBA) {
        return FW_INVALID_PPA;
    }
    return ftl->l2p[lba];
}

