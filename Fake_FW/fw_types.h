#ifndef FW_TYPES_H
#define FW_TYPES_H

#include "conf.h"

#include <stdbool.h>
#include <stdint.h>

#define FW_PAGE_SIZE 256u
#define FW_PAGES_PER_BLOCK 8u
#define FW_BLOCK_COUNT 16u
#define FW_TOTAL_PAGES (FW_PAGES_PER_BLOCK * FW_BLOCK_COUNT)
#define FW_MAX_LBA FW_TOTAL_PAGES
#define FW_CACHE_LINES 8u
#define FW_QUEUE_DEPTH 8u
#define FW_INVALID_PPA 0xFFFFFFFFu

typedef enum fw_status {
    FW_OK = 0,
    FW_ERR = -1,
    FW_ERR_RANGE = -2,
    FW_ERR_NAND = -3,
    FW_ERR_BUSY = -4,
    FW_ERR_NO_SPACE = -5
} fw_status_t;

typedef enum ssd_io_type {
    SSD_IO_READ = 0,
    SSD_IO_WRITE = 1,
    SSD_IO_FLUSH = 2
} ssd_io_type_t;

typedef struct ssd_request {
    uint32_t lba;
    uint32_t length;
    uint8_t *buffer;
    ssd_io_type_t type;
    fw_status_t status;
} ssd_request_t;

typedef struct nand_page {
    uint8_t data[FW_PAGE_SIZE];
    bool valid;
} nand_page_t;

static inline uint32_t fw_block_of_page(uint32_t ppa)
{
    return ppa / FW_PAGES_PER_BLOCK;
}

#endif
