#include "nvme.h"

#include "fw_log.h"

void nvme_controller_init(nvme_controller_t *ctrl)
{
    ctrl->state = NVME_STATE_RESET;
    nand_init(&ctrl->nand);
    cache_init(&ctrl->cache);
    gc_init(&ctrl->gc);
    wear_level_init(&ctrl->wl);
    bad_block_init(&ctrl->bbm);
    ftl_init(&ctrl->ftl, &ctrl->nand, &ctrl->cache, &ctrl->gc, &ctrl->wl, &ctrl->bbm);
    scheduler_init(&ctrl->queue);
    ctrl->state = NVME_STATE_READY;
}

fw_status_t nvme_submit_read(nvme_controller_t *ctrl, uint32_t lba, uint8_t *buffer)
{
    ssd_request_t request = {
        .lba = lba,
        .length = 1,
        .buffer = buffer,
        .type = SSD_IO_READ,
        .status = FW_OK,
    };
    return scheduler_enqueue(&ctrl->queue, &request);
}

fw_status_t nvme_submit_write(nvme_controller_t *ctrl, uint32_t lba, const uint8_t *buffer)
{
    ssd_request_t request = {
        .lba = lba,
        .length = 1,
        .buffer = (uint8_t *)buffer,
        .type = SSD_IO_WRITE,
        .status = FW_OK,
    };
    return scheduler_enqueue(&ctrl->queue, &request);
}

fw_status_t nvme_poll(nvme_controller_t *ctrl)
{
    if (ctrl->state != NVME_STATE_READY) {
        return FW_ERR_BUSY;
    }

    while (scheduler_has_pending(&ctrl->queue)) {
        fw_status_t status = scheduler_process(&ctrl->queue, &ctrl->ftl);
        if (status != FW_OK) {
            fw_log(FW_LOG_ERROR, "nvme", fw_status_name(status));
            ctrl->state = NVME_STATE_ERROR;
            return status;
        }
    }
    return FW_OK;
}

