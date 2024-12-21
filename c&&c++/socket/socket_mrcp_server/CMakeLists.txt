cmake_minimum_required(VERSION 3.20)
project(socket_mrcp_server C)

set(CMAKE_C_STANDARD 11)

add_executable(mrcp_asr_server socket_server_mutile.c mrcp_asr_server.c)

# 链接动态库
target_link_libraries(mrcp_asr_server pthread)

add_definitions(-g3 -O0)
