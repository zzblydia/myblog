cmake_minimum_required(VERSION 3.25)
project(socket_mrcp_server C)

set(CMAKE_C_STANDARD 11)

add_executable(mrcp_asr_server socket_server_mutile.c mrcp_asr_server.c)
