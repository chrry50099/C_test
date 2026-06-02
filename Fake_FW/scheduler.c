#include "scheduler.h"

void scheduler_init(scheduler_queue_t *queue)
{
    queue->head = 0;
    queue->tail = 0;
    queue->count = 0;
}

fw_status_t scheduler_enqueue(scheduler_queue_t *queue, const ssd_request_t *request)
{
    if (queue->count >= FW_QUEUE_DEPTH) {
        return FW_ERR_BUSY;
    }
    queue->requests[queue->tail] = *request;
    queue->tail = (queue->tail + 1u) % FW_QUEUE_DEPTH;
    queue->count++;
    return FW_OK;
}

fw_status_t scheduler_process(scheduler_queue_t *queue, ftl_context_t *ftl)
{
    if (queue->count == 0) {
        return FW_OK;
    }

    ssd_request_t *request = &queue->requests[queue->head];
    fw_status_t status = FW_ERR;

    switch (request->type) {
    case SSD_IO_READ:
        status = ftl_read(ftl, request->lba, request->buffer);
        break;
    case SSD_IO_WRITE:
        status = ftl_write(ftl, request->lba, request->buffer);
        break;
    /* BUG_HINT: SSD_IO_FLUSH is defined but scheduler_process does not handle it. */
    default:
        status = FW_ERR;
        break;
    }

    request->status = status;
    queue->head = (queue->head + 1u) % FW_QUEUE_DEPTH;
    queue->count--;
    return status;
}

bool scheduler_has_pending(const scheduler_queue_t *queue)
{
    return queue->count != 0u;
}

