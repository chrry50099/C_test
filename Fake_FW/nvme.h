#ifndef NVME_H
#define NVME_H

#include "scheduler.h"

typedef enum nvme_state {
    NVME_STATE_RESET = 0,
    NVME_STATE_READY = 1,
    NVME_STATE_ERROR = 2
} nvme_state_t;

typedef struct nvme_controller {
    nvme_state_t state;
    scheduler_queue_t queue;
    ftl_context_t ftl;
    nand_device_t nand;
    cache_context_t cache;
    gc_context_t gc;
    wear_level_context_t wl;
    bad_block_manager_t bbm;
} nvme_controller_t;

void nvme_controller_init(nvme_controller_t *ctrl);
fw_status_t nvme_submit_read(nvme_controller_t *ctrl, uint32_t lba, uint8_t *buffer);
fw_status_t nvme_submit_write(nvme_controller_t *ctrl, uint32_t lba, const uint8_t *buffer);
fw_status_t nvme_poll(nvme_controller_t *ctrl);

#endif

