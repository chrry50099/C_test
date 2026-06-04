#include "nvme.h"

#include "fw_ext_registry.h"
#include "fw_log.h"

#include <stdio.h>
#include <string.h>

int main(void)
{
    nvme_controller_t ctrl;
    fw_ext_registry_t ext_registry = {0};
    uint8_t write_buf[FW_PAGE_SIZE];
    uint8_t read_buf[FW_PAGE_SIZE];

    memset(write_buf, 0x5A, sizeof(write_buf));
    memset(read_buf, 0, sizeof(read_buf));

    nvme_controller_init(&ctrl);
    fw_ext_registry_bootstrap(&ext_registry);
    fw_log(FW_LOG_INFO, "boot", FW_CPU_NAME);

#if FW_ENABLE_NVME_FRONTEND
    fw_status_t submit_status = nvme_submit_write(&ctrl, 4, write_buf);
    if (submit_status != FW_OK) {
        FW_LOG_FAIL("submit_write");
        return 1;
    }
    nvme_poll(&ctrl);

    submit_status = nvme_submit_read(&ctrl, 4, read_buf);
    if (submit_status != FW_OK) {
        FW_LOG_FAIL("submit_read");
        return 1;
    }
    nvme_poll(&ctrl);

    printf("read_buf[0]=0x%02X\n", read_buf[0]);
    (void)fw_ext_registry_poll(&ext_registry, read_buf[0]);
#else
    fw_status_t submit_status = nvme_poll(&ctrl);
    (void)fw_ext_registry_poll(&ext_registry, submit_status == FW_OK ? 1u : 0u);
    printf("gc worker poll status=%s\n", fw_status_name(submit_status));
#endif
    return 0;
}
