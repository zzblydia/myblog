---
title:  "laptop get battery report"
date:   2023-12-26 21:26:26 +0800
last_modified_at: 2024-05-02 22:27:00 +0800
categories: windows
tags: windows
---

# 笔记本电脑获取电池报告  

## 背景  
笔记本电脑电池寿命到了, 开始充不上电了. 换新电池之前简单研究了下电池使用历史.  

## 命令和环境  
环境: windows 10  

```
以下命令保存为.bat文件, 默认输出到路径D:\  

powercfg /batteryreport /output "D:\%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%_battery_report.html"

pause
```

## 重点参数示例解读  
```
DESIGN CAPACITY	        48,614 mWh
FULL CHARGE CAPACITY    19,388 mWh
CYCLE COUNT	        79
```