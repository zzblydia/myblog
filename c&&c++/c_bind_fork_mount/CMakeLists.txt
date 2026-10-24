# mount_guard 构建脚本
#
# 推荐用法(在源码目录执行, 产物隔离在 build/ 下):
#   cmake -S . -B build && cmake --build build -j
# 或者要求直接在源码目录用 make:
#   cmake . && make
#
# 清理: cmake --build build --target clean, 或直接删除 build/ 目录

cmake_minimum_required(VERSION 3.10)

project(mount_guard C)

# 未指定构建类型时默认 Release, 避免生成无优化的默认构建
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# 使用 C11 且关闭 GNU 扩展, 与手工编译时的 -std=c11 保持一致
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# 保持与手工编译一致的优化级别(CMake 默认 Release 为 -O3)
set(CMAKE_C_FLAGS_RELEASE "-O2 -DNDEBUG")

# 方案 2(默认): 监听 fd 带 SOCK_CLOEXEC, 端口只归本进程
add_executable(mount_guard mount_guard.c)

# 方案 1: 监听 fd 被子进程继承, 用于验证 timeout 的回收行为
add_executable(mount_guard_tmo mount_guard.c)
target_compile_definitions(mount_guard_tmo PRIVATE USE_CLOEXEC=0)

# 只在 GCC/Clang 下追加告警选项, 避免其他编译器报未知参数
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(mount_guard PRIVATE -Wall -Wextra)
    target_compile_options(mount_guard_tmo PRIVATE -Wall -Wextra)
endif()
