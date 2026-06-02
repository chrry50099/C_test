cmake_minimum_required(VERSION 3.20)

project(fake_ssd_fw C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_executable(fake_ssd_fw
    main.c
    fw_log.c
    nand.c
    ftl.c
    gc.c
    wear_level.c
    bad_block.c
    cache.c
    scheduler.c
    nvme.c
)

target_include_directories(fake_ssd_fw PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

