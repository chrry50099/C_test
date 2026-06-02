#ifndef CONF_H
#define CONF_H

#define FW_CPU0 0
#define FW_CPU1 1

#ifndef FW_CPU_ID
#define FW_CPU_ID FW_CPU0
#endif

#if FW_CPU_ID == FW_CPU0
#define FW_ENABLE_NVME_FRONTEND 1
#define FW_ENABLE_GC_WORKER 0
#define FW_CPU_NAME "CPU0"
#elif FW_CPU_ID == FW_CPU1
#define FW_ENABLE_NVME_FRONTEND 0
#define FW_ENABLE_GC_WORKER 1
#define FW_CPU_NAME "CPU1"
#else
#error "Unsupported FW_CPU_ID"
#endif

#define FW_CPU_IS(cpu_id) (FW_CPU_ID == (cpu_id))

#endif

