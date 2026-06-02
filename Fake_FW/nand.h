#ifndef NAND_H
#define NAND_H

#include "fw_types.h"

typedef struct nand_device {
    nand_page_t pages[FW_TOTAL_PAGES];
    uint8_t bad_blocks[FW_BLOCK_COUNT];
    uint16_t erase_count[FW_BLOCK_COUNT];
} nand_device_t;

void nand_init(nand_device_t *dev);
fw_status_t nand_read_page(nand_device_t *dev, uint32_t ppa, uint8_t *buffer);
fw_status_t nand_program_page(nand_device_t *dev, uint32_t ppa, const uint8_t *buffer);
fw_status_t nand_erase_block(nand_device_t *dev, uint32_t block);
void nand_mark_bad(nand_device_t *dev, uint32_t block);
bool nand_is_bad(const nand_device_t *dev, uint32_t block);

#endif

