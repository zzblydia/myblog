cmake_minimum_required(VERSION 3.25)
include(CheckFunctionExists)
project(openssl_test C)

set(CMAKE_C_STANDARD 11)

#set(OPENSSL_VERSION_FOLDER "opens07fa59b597942") # 1.1.1w
set(OPENSSL_VERSION_FOLDER "opens4050fb5d6d9ea") # 3.0.12
set(OPENSSL_ROOT_DIR "C:/Users/vmwin10/.conan2/p/${OPENSSL_VERSION_FOLDER}/p/")
find_package(OpenSSL REQUIRED)
if (OPENSSL_FOUND)
    message("OPENSSL_VERSION: ${OPENSSL_VERSION}")
    message("OPENSSL_INCLUDE_DIR: ${OPENSSL_INCLUDE_DIR}")
    message("OPENSSL_LIBRARIES: ${OPENSSL_LIBRARIES}")
endif ()

set(LIB_LIST "ws2_32.lib;userenv.lib;psapi.lib;iphlpapi.lib;crypt32.lib")
list(INSERT LIB_LIST 0 ${OPENSSL_LIBRARIES})

set(CMAKE_REQUIRED_INCLUDES ${OPENSSL_INCLUDE_DIR})
set(CMAKE_REQUIRED_LIBRARIES ${LIB_LIST})
message("CMAKE_REQUIRED_INCLUDES: ${CMAKE_REQUIRED_INCLUDES}")
message("CMAKE_REQUIRED_LIBRARIES: ${CMAKE_REQUIRED_LIBRARIES}")
CHECK_FUNCTION_EXISTS(HMAC_CTX_new LWS_HAVE_HMAC_CTX_new)

link_libraries(crypto)
add_executable(openssl_test main.c)
