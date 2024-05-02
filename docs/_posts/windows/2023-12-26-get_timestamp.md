---
title:  "get timestamp on windows"
date:   2023-12-26 21:26:26 +0800
last_modified_at: 2024-05-03 03:54:00 +0800
categories: windows
tags: 
  - windows
  - timestamp
---

# windows10下获取时间戳的两种方式

## 环境  
OS: windows10  
timezone: HK  

### 方式一:  
command: date /t ---> 2023/12/16 周六  
command: time    ---> 20:39:07.71  
commadn: time    ---> 3:47:40.68 ---->小时为一位数  

```
@echo off
rem /f 表示对一个文件或者一个命令的输出进行处理  
rem "tokens=1-3 delims=/ " 按照 / 和空格来分割 %date% 的值  
rem "tokens=1-4 delims=:." 按照 : . 和空格来分割 %time% 的值  

rem get date
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do (
  set year=%%a
  set month=%%b
  set day=%%c
)
rem echo date:%year%%month%%day%

rem get time
for /f "tokens=1-4 delims=:." %%a in ("%time%") do (
  set hour=%%a
  set minute=%%b
  set second=%%c
  set millisecond=%%d
)
rem echo time:%hour%%minute%%second%_%millisecond%

set timestamp=%year%%month%%day%_%hour%%minute%%second%
echo timestamp:%timestamp%

pause
```

### 方式二:  
```
rem 解决方式一中time 0到11点时小时数值前有空格  
rem %date:~0,4%：从%date% 变量中提取子字符串。~0,4 表示从字符串的第一个字符开始（索引从0开始），取4个字符  
echo timestamp_simple:%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%  

if %time:~0,2% LEQ 9 (echo timestamp_simple:%date:~0,4%%date:~5,2%%date:~8,2%_0%time:~1,1%%time:~3,2%%time:~6,2%) else (echo timestamp_simple:%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%)

pause
```

### 细节  
[get_timestamp_on_windows10](https://github.com/zzblydia/myBlog/blob/master/windows/get_timestamp.cmd)  