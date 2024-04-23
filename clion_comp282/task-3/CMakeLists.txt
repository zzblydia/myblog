cmake_minimum_required(VERSION 3.25)
project(comp282)

set(CMAKE_CXX_STANDARD 11)

add_executable(comp282 AdventureGame.cpp Item.cpp Character.cpp Location.cpp debug.cpp)
