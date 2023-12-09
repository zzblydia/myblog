cmake_minimum_required(VERSION 3.25)
project(openssl_test C)

set(CMAKE_C_STANDARD 11)

include_directories(
        # "C:/Program Files/OpenSSL-Win64-1.1.1w/include"
        "C:/Program Files/OpenSSL-Win64/include"
)

link_directories(
        # "C:/Program Files/OpenSSL-Win64-1.1.1w/lib"
        "C:/Program Files/OpenSSL-Win64/lib"
)

link_libraries(crypto)

add_executable(openssl_test main.c)
