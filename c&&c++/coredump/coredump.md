# 速记  

##  core file  
core - core dump file 核心转储文件.  
某些信号的[coredump_test.c](coredump_test.c)默认操作是导致进程终止并生成核心转储文件，该文件包含终止时进程内存的映像。  
此映像可用于调试器（例如gdb (1)）来检查程序终止时的状态。 

## 生成core文件的前提  
1.ulimit -c显示的结果不为0.  
2.生成路径有可写权限.  
3.生成路径下有无法覆盖的文件, 或者同名软连接,目录  

## 生成core文件的名称格式  
受系统文件/proc/sys/kernel/core_pattern配置, 可用的参数:  
echo "/corefiles/core.%e.%t.%h.%p.%s" | sudo tee /proc/sys/kernel/core_pattern  

- %e：可执行文件名（不带路径）。
- %t：时间戳（自1970年1月1日以来的秒数）。
- %h：主机名。
- %p：进程ID。
- %s：信号编号。

## 生成core文件的内容控制  
/proc/PID/coredump_filter 的值是一个十六进制显示的位掩码, 表示不同类型的内存区域.  
 - bit 0  Dump anonymous private mappings.
 - bit 1  Dump anonymous shared mappings.
 - bit 2  Dump file-backed private mappings.
 - bit 3  Dump file-backed shared mappings.
 - bit 4 (since Linux 2.6.24) Dump ELF headers.
 - bit 5 (since Linux 2.6.28) Dump private huge pages.
 - bit 6 (since Linux 2.6.28) Dump shared huge pages.
 - bit 7 (since Linux 4.4)    Dump private DAX pages.
 - bit 8 (since Linux 4.4)    Dump shared DAX pages.

比如关闭 bit 1可以不转储进程的共享内存.  

## FAQ  
1.可以使用命令**man core**查看 core 相关的man手册页  
2.ubuntu-24.04 /proc/sys/kernel/core_pattern:  
|/usr/share/apport/apport -p%p -s%s -c%c -d%d -P%P -u%u -g%g -- %E  

## TODO  
1. https://www.cnblogs.com/arnoldlu/p/9633254.html#core_gdb  
2. coredumpctl  
3. sigaction  
4. getrlimit  
5. 

## preference
1. [ubuntu core](https://manpages.ubuntu.com/manpages/noble/man5/core.5.html)

