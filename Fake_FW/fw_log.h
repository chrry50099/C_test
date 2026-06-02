#ifndef FW_LOG_H
#define FW_LOG_H

#include "fw_types.h"

typedef enum fw_log_level {
    FW_LOG_INFO = 0,
    FW_LOG_WARN = 1,
    FW_LOG_ERROR = 2
} fw_log_level_t;

#define FW_LOG_OK(tag) fw_log(FW_LOG_INFO, tag, "ok")
#define FW_LOG_FAIL(tag) fw_log(FW_LOG_ERROR, tag, "failed")

void fw_log(fw_log_level_t level, const char *tag, const char *message);
const char *fw_status_name(fw_status_t status);

#endif

