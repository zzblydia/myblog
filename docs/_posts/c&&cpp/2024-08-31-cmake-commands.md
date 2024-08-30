---
title:  "cmake commands"
date:   2024-08-31 00:44:00 +0800
last_modified_at: 2024-08-31 01:11:00 +0800
categories: cmake
tags: cmake
---

# some notes of cmake  

## 1. common usage
1> **cmake .. -DCMAKE_VERBOSE_MAKEFILE=ON**  
This option tells CMake to generate a verbose Makefile.  
When you run make, it will display each compilation and linking step, which is very useful for debugging the build process.  

2> **cmake .. --trace-expand**  
This option enables tracing, which means that every command executed by CMake during configuration will be printed, along with all relevant variables expanded to their actual values at that moment.  
This is particularly useful for debugging complex configurations and understanding how variables affect the build process.  

3> **cmake .. -DCMAKE_BUILD_TYPE=type**  
This option sets the build type, which can affect compiler flags and optimizations. Common values for `type` include:  

(1)Debug: Enables debugging information and disables optimizations. (maybe **-g**)  
(2)Release: Enables optimizations and disables debugging information. (maybe **-O3 -DNDEBUG**)  
(3)RelWithDebInfo: Combines optimization with debugging information. (maybe **-O2 -g -DNDEBUG**)  
(4)MinSizeRel: Optimizes for minimum size. (maybe **-Os -DNDEBUG**)  

## 2. Reference  
[cmake latest document](https://cmake.org/cmake/help/latest/manual/cmake.1.html)
