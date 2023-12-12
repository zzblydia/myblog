cmake_minimum_required(VERSION 3.25)
include(CheckFunctionExists)
project(openssl_test C)

set(CMAKE_C_STANDARD 11)

find_package(OpenSSL REQUIRED)
if (OPENSSL_FOUND)
    message("OPENSSL_VERSION: ${OPENSSL_VERSION}")
    message("OPENSSL_INCLUDE_DIR: ${OPENSSL_INCLUDE_DIR}")
    message("OPENSSL_LIBRARIES: ${OPENSSL_LIBRARIES}")
    set(PUBLIC_INCLUDE_DIRS "${OPENSSL_INCLUDE_DIR}")
    set(PUBLIC_LIBRARIES ${OPENSSL_LIBRARIES})
endif ()

message("LWS_OPENSSL_INCLUDE_DIRS: ${LWS_OPENSSL_INCLUDE_DIRS}")
message("LWS_OPENSSL_LIBRARIES: ${LWS_OPENSSL_LIBRARIES}")
set(PUBLIC_INCLUDE_DIRS "${LWS_OPENSSL_INCLUDE_DIRS}")
set(PUBLIC_LIBRARIES ${LWS_OPENSSL_LIBRARIES})

if (DEFINED PUBLIC_INCLUDE_DIRS)
    set(CMAKE_REQUIRED_INCLUDES ${PUBLIC_INCLUDE_DIRS})
    message("CMAKE_REQUIRED_INCLUDES: ${CMAKE_REQUIRED_INCLUDES}")
endif()
if (DEFINED PUBLIC_LIBRARIES)
    set(CMAKE_REQUIRED_LIBRARIES ${PUBLIC_LIBRARIES})
    message("CMAKE_REQUIRED_LIBRARIES: ${CMAKE_REQUIRED_LIBRARIES}")
endif()
CHECK_FUNCTION_EXISTS(HMAC_CTX_new LWS_HAVE_HMAC_CTX_new)

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
