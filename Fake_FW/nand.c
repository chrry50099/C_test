#include "nand.h"

#include <string.h>

void nand_init(nand_device_t *dev)
{
    memset(dev, 0, sizeof(*dev));
    for (uint32_t page = 0; page < FW_TOTAL_PAGES; page++) {
        memset(dev->pages[page].data, 0xFF, FW_PAGE_SIZE);
        dev->pages[page].valid = false;
    }
}

fw_status_t nand_read_page(nand_device_t *dev, uint32_t ppa, uint8_t *buffer)
{
    if (dev == 0 || buffer == 0 || ppa >= FW_TOTAL_PAGES) {
        return FW_ERR_RANGE;
    }
    if (nand_is_bad(dev, fw_block_of_page(ppa))) {
        return FW_ERR_NAND;
    }

    memcpy(buffer, dev->pages[ppa].data, FW_PAGE_SIZE);
    return FW_OK;
}

fw_status_t nand_program_page(nand_device_t *dev, uint32_t ppa, const uint8_t *buffer)
{
    if (dev == 0 || buffer == 0 || ppa >= FW_TOTAL_PAGES) {
        return FW_ERR_RANGE;
    }
    if (nand_is_bad(dev, fw_block_of_page(ppa))) {
        return FW_ERR_NAND;
    }

    memcpy(dev->pages[ppa].data, buffer, FW_PAGE_SIZE);
    dev->pages[ppa].valid = true;
    return FW_OK;
}

fw_status_t nand_erase_block(nand_device_t *dev, uint32_t block)
{
    if (dev == 0 || block >= FW_BLOCK_COUNT) {
        return FW_ERR_RANGE;
    }
    if (nand_is_bad(dev, block)) {
        return FW_ERR_NAND;
    }

    uint32_t first_page = block * FW_PAGES_PER_BLOCK;
    for (uint32_t offset = 0; offset < FW_PAGES_PER_BLOCK; offset++) {
        uint32_t page = first_page + offset;
        memset(dev->pages[page].data, 0xFF, FW_PAGE_SIZE);
        dev->pages[page].valid = false;
    }
    dev->erase_count[block]++;
    return FW_OK;
}

void nand_mark_bad(nand_device_t *dev, uint32_t block)
{
    if (dev != 0 && block < FW_BLOCK_COUNT) {
        dev->bad_blocks[block] = 1u;
    }
}

bool nand_is_bad(const nand_device_t *dev, uint32_t block)
{
    return dev == 0 || block >= FW_BLOCK_COUNT || dev->bad_blocks[block] != 0u;
}

