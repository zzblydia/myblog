---
title:  "gdb commands"
date:   2023-12-12 06:33:33 +0800
last_modified_at: 2024-08-31 20:41:00 +0800
categories: gdb
tags: gdb
---

# some notes of gdb  

The explanations are provided by ChatGPT-4o.  

## attach  
```
gcc -g -o helloworld helloworld.c &&　./helloworld &
ps -ef | grep helloworld
gdb helloworld
b main
attach pid
```

## handle  
```
handle SIGTERM nostop  
handle SIG36 nostop noprint  
handle SIG35 nostop noprint  
```
nostop 选项告诉 gdb 在接收到信号时不要停止程序的执行。  
noprint 选项告诉 gdb 在接收到信号时不要打印任何信息。  

## command  
```
break function  
command  
bt 20  
c  
end  
attach pid  
```
command：开始定义断点命令列表。这个列表中的命令将在断点命中时自动执行。  
bt 20：显示当前调用堆栈的前 20 帧。bt 是 backtrace 的缩写。  

## temp variable  
```
set $tmp = 0  
set $tmp = $tmp + 1  
```
set $tmp = 0：在 gdb 中创建一个名为 $tmp 的用户定义变量，并将其初始化为 0。用户定义的变量名以 $ 开头。  
set $tmp = $tmp + 1：将 $tmp 的值增加 1。这是一个简单的自增操作。  
 
## watch  
```
watch/rwatch/awatch g_timesCount  
command  
bt 20  
c  
end  
```
获取全局变量访问的堆栈信息.  
watch g_timesCount：设置一个写观察点，当 g_timesCount 变量的值发生变化时，程序会暂停。  
rwatch g_timesCount：设置一个读观察点，当 g_timesCount 变量被读取时，程序会暂停。  
awatch g_timesCount：设置一个访问观察点，当 g_timesCount 变量被读取或写入时，程序会暂停。  

## break  
```
b function if (input para == 3)  
command  
set $count = 0  
c  
end  
b file:line if ($count % 2 == 0)  
command  
p $count  
end  
```
b function if (input para == 3)：在 function 函数处设置一个条件断点，只有当 input para 等于 3 时，程序才会在该断点处暂停。  
set $count = 0：在 gdb 中创建一个名为 $count 的用户定义变量，并将其初始化为 0。  
b file:line if ($count % 2 == 0)：在指定的文件和行号处设置一个条件断点，只有当 $count 是偶数时，程序才会在该断点处暂停  

## x
```
x/200bx
```
x: 这是 gdb 中的“检查内存”（examine memory）命令。  
/200: 这是一个可选的重复计数，表示要显示的内存单元的数量。在这个例子中，200 表示要显示 200 个内存单元。  
b: 这是一个格式说明符，表示每个内存单元的大小。b 代表字节（byte）。  
x: 这是另一个格式说明符，表示内存单元的显示格式。x 代表十六进制（hexadecimal）  

## catch  
```
catch syscall exit_group
```
exit_group是Linux系统中的一个系统调用，用于终止当前进程及其所有线程。通过捕获这个系统调用，你可以观察到程序何时准备退出.  

## batch  
```
gdb --batch -ex "p g_times" -p PID  
```

