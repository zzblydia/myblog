cmake_minimum_required(VERSION 3.25)
project(ws-server-simple-send-recv-tls)

# 设置C编译器
set(CMAKE_C_COMPILER gcc)

# 添加头文件目录
include_directories(/opt/openssl/include /usr/local/include)

# 添加库文件目录
link_directories(/opt/openssl/lib64 /usr/local/lib)

# 添加可执行文件
add_executable(ws-server-simple-send-recv-tls ws-server-simple-send-recv-tls.c)

# 添加链接库
target_link_libraries(ws-server-simple-send-recv-tls libwebsockets.so)

# 添加编译选项
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -g3 -O0")