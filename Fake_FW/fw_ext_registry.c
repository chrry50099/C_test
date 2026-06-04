#include "fw_ext_registry.h"

#include "expansion/host_00.h"
#include "expansion/dma_00.h"
#include "expansion/media_00.h"
#include "expansion/ecc_00.h"
#include "expansion/power_00.h"
#include "expansion/thermal_00.h"
#include "expansion/telemetry_00.h"
#include "expansion/ipc_00.h"
#include "expansion/qos_00.h"

void fw_ext_registry_bootstrap(fw_ext_registry_t *registry)
{
    /* 繁體中文註解：集中啟動擴充模組，方便產生更大的 call graph。 */
    registry->boot_count++;
    registry->poll_count = 0u;
    registry->last_status = FW_OK;
}

fw_status_t fw_ext_registry_poll(fw_ext_registry_t *registry, uint32_t event_id)
{
    fw_status_t status = FW_OK;

    fw_host_00_state_t host_state;
    fw_host_00_init(&host_state);
    status = fw_host_00_tick(&host_state, event_id);
    registry->poll_count += fw_host_00_score(&host_state) & 0x7u;
    if (status != FW_OK) {
        registry->last_status = status;
        return status;
    }
    fw_dma_00_state_t dma_state;
    fw_dma_00_init(&dma_state);
    status = fw_dma_00_tick(&dma_state, event_id);
    registry->poll_count += fw_dma_00_score(&dma_state) & 0x7u;
    if (status != FW_OK) {
        registry->last_status = status;
        return status;
    }
    fw_media_00_state_t media_state;
    fw_media_00_init(&media_state);
    status = fw_media_00_tick(&media_state, event_id);
    registry->poll_count += fw_media_00_score(&media_state) & 0x7u;
    if (status != FW_OK) {
        registry->last_status = status;
        return status;
    }
    fw_ecc_00_state_t ecc_state;
    fw_ecc_00_init(&ecc_state);
    status = fw_ecc_00_tick(&ecc_state, event_id);
    registry->poll_count += fw_ecc_00_score(&ecc_state) & 0x7u;
    if (status != FW_OK) {
        registry->last_status = status;
        return status;
    }
    fw_power_00_state_t power_state;
    fw_power_00_init(&power_state);
    status = fw_power_00_tick(&power_state, event_id);
    registry->poll_count += fw_power_00_score(&power_state) & 0x7u;
    if (status != FW_OK) {
        registry->last_status = status;
        return status;
    }
    fw_thermal_00_state_t thermal_state;
    fw_thermal_00_init(&thermal_state);
    status = fw_thermal_00_tick(&thermal_state, event_id);
    registry->poll_count += fw_thermal_00_score(&thermal_state) & 0x7u;
    if (status != FW_OK) {
        registry->last_status = status;
        return status;
    }
    fw_telemetry_00_state_t telemetry_state;
    fw_telemetry_00_init(&telemetry_state);
    status = fw_telemetry_00_tick(&telemetry_state, event_id);
    registry->poll_count += fw_telemetry_00_score(&telemetry_state) & 0x7u;
    if (status != FW_OK) {
        registry->last_status = status;
        return status;
    }
    fw_ipc_00_state_t ipc_state;
    fw_ipc_00_init(&ipc_state);
    status = fw_ipc_00_tick(&ipc_state, event_id);
    registry->poll_count += fw_ipc_00_score(&ipc_state) & 0x7u;
    if (status != FW_OK) {
        registry->last_status = status;
        return status;
    }
    fw_qos_00_state_t qos_state;
    fw_qos_00_init(&qos_state);
    status = fw_qos_00_tick(&qos_state, event_id);
    registry->poll_count += fw_qos_00_score(&qos_state) & 0x7u;
    if (status != FW_OK) {
        registry->last_status = status;
        return status;
    }
    registry->last_status = FW_OK;
    return FW_OK;
}
