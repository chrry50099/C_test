#ifndef WEAR_LEVEL_H
#define WEAR_LEVEL_H

#include "nand.h"

typedef struct wear_level_context {
    uint16_t high_watermark;
    uint16_t low_watermark;
} wear_level_context_t;

void wear_level_init(wear_level_context_t *wl);
void wear_level_record_erase(wear_level_context_t *wl, nand_device_t *dev, uint32_t block);
uint32_t wear_level_select_cold_block(const wear_level_context_t *wl, const nand_device_t *dev);
bool wear_level_needs_rotation(const wear_level_context_t *wl, const nand_device_t *dev);

#endif

