#include "fw_log.h"

#include <stdio.h>

void fw_log(fw_log_level_t level, const char *tag, const char *message)
{
    const char *prefix = "INFO";

    if (level == FW_LOG_WARN) {
        prefix = "WARN";
    } else if (level == FW_LOG_ERROR) {
        prefix = "ERROR";
    }

    printf("[%s] %s: %s\n", prefix, tag, message);
}

const char *fw_status_name(fw_status_t status)
{
    switch (status) {
    case FW_OK:
        return "FW_OK";
    case FW_ERR_RANGE:
        return "FW_ERR_RANGE";
    case FW_ERR_NAND:
        return "FW_ERR_NAND";
    case FW_ERR_BUSY:
        return "FW_ERR_BUSY";
    case FW_ERR_NO_SPACE:
        return "FW_ERR_NO_SPACE";
    default:
        return "FW_ERR";
    }
}

