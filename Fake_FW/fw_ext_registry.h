#ifndef FW_EXT_REGISTRY_H
#define FW_EXT_REGISTRY_H

#include "fw_types.h"

typedef struct fw_ext_registry {
    uint32_t boot_count;
    uint32_t poll_count;
    fw_status_t last_status;
} fw_ext_registry_t;

void fw_ext_registry_bootstrap(fw_ext_registry_t *registry);
fw_status_t fw_ext_registry_poll(fw_ext_registry_t *registry, uint32_t event_id);

#endif
