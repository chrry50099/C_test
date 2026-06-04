cmake_minimum_required(VERSION 3.20)

project(fake_ssd_fw C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

file(GLOB_RECURSE FAKE_SSD_FW_EXPANSION_SOURCES CONFIGURE_DEPENDS
    ${CMAKE_CURRENT_SOURCE_DIR}/expansion/*.c
)

set(FAKE_SSD_FW_SOURCES
    main.c
    fw_log.c
    fw_ext_registry.c
    nand.c
    ftl.c
    gc.c
    wear_level.c
    bad_block.c
    cache.c
    scheduler.c
    nvme.c
    ${FAKE_SSD_FW_EXPANSION_SOURCES}
)

add_executable(fake_ssd_fw_cpu0 ${FAKE_SSD_FW_SOURCES})
target_include_directories(fake_ssd_fw_cpu0 PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(fake_ssd_fw_cpu0 PRIVATE FW_CPU_ID=0)

add_executable(fake_ssd_fw_cpu1 ${FAKE_SSD_FW_SOURCES})
target_include_directories(fake_ssd_fw_cpu1 PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(fake_ssd_fw_cpu1 PRIVATE FW_CPU_ID=1)

add_executable(fake_ssd_fw ALIAS fake_ssd_fw_cpu0)
