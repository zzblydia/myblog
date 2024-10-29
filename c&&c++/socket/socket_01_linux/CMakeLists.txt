cmake_minimum_required(VERSION 3.25)
project(socket_01 C)

set(CMAKE_C_STANDARD 11)

add_executable(socket_client socket_client.c)
add_executable(socket_server socket_server.c)
