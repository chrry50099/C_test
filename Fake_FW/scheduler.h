#ifndef SCHEDULER_H
#define SCHEDULER_H

#include "ftl.h"

typedef struct scheduler_queue {
    ssd_request_t requests[FW_QUEUE_DEPTH];
    uint32_t head;
    uint32_t tail;
    uint32_t count;
} scheduler_queue_t;

void scheduler_init(scheduler_queue_t *queue);
fw_status_t scheduler_enqueue(scheduler_queue_t *queue, const ssd_request_t *request);
fw_status_t scheduler_process(scheduler_queue_t *queue, ftl_context_t *ftl);
bool scheduler_has_pending(const scheduler_queue_t *queue);

#endif

