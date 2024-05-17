---
title:  "batch rename files"
date:   2024-05-12 08:05:00 +0800
last_modified_at: 2024-05-12 15:48:00 +0800
categories: windows
---

# bat脚本批量重命名  

## 背景  
下载的视频文件名称不符合plex的搜刮要求, 通过脚本批量重命名.  
old name format: [晨曦制作&老M][艾斯奥特曼][52][未来的艾斯是你!][中日双字幕][BDrip][HEVC Main10P FLAC MKV].mkv  
new name format: 艾斯奥特曼_52.mkv  

## 需求拆分  
1.设置路径变量folder_path, 并获取路径下所有文件.  
2.遍历所有文件, 获取文件名file_name, 提取第2个[]和第3个[]的内容拼接new_name.  
3.重命名文件 ren folder_path\file_name folder_path\new_name  

## 过程  
打开chatgpt, 输入如下:  
在windows环境下, 请写一个bat脚本, 用于批量重命名文件.原始文件名由多个[]组成, 目标文件名由第2/3个[]的内容组成.  

chatgpt不假思索, 劈里啪啦就写了一堆代码, 一气呵成.  
从开发的角度, 在执行ren之前打印下原始文件名和目标文件名, 判断下执行过程.  

```
@echo off
setlocal enabledelayedexpansion
set "folder_path=E:\plex\test\"

for %%f in ("%folder_path%\*.mkv") do (
    rem 获取文件名
    set "file_name=%%~nxf"
    echo "!file_name!"
    
    rem 解析文件名中的第2和第3个[]里面的内容
    for /f "tokens=2,3 delims=[]" %%a in ("!file_name!") do (
        set "old_name=!folder_path!!file_name!"
        set "new_name=!folder_path!%%a_%%b."
        echo old_name "!old_name!" 
        echo new name "!new_name!"
        
        ren "!old_name!" "!new_name!"
    )
)
endlocal
pause
``` 

找了个文件夹, 放了一个视频文件进去, 测试一把OK.  
放到正式文件夹里执行完一看, 只有大概一半文件按照预期完成了, 其他文件没动...  
经过反复执行, 发现处理剩下文件都报错"系统找不到指定的文件",  
***经过反复测试, 发现未处理的文件的文件名中都包含了感叹号...***  

## 探索  
chatgpt说是enabledelayedexpansion启用了延迟扩展导致的, 该选项启用后可以使用!file_name!等用法.  
禁用后重写如下:
```
@echo off
set "target_dir=C:\path\to\your\directory"
for %%F in ("%target_dir%\*.mkv") do (
    for /F "tokens=2,3 delims=[]" %%G in ("%%~nxF") do (
        ren "%%F" "%%G_%%H.mkv"
    )
)
```
for /F "tokens=2,3 delims=[]" %%G in ("%%~nxF") do (：这条命令开始了另一个循环，它解析当前文件名（不包括路径），并提取出第二个和第三个[]之间的内容。这些内容将被存储在变量%%G和%%H中。   

***自测试OK, 正常处理了异常的文件, 并且已处理的文件未受影响.***  

## 感受  
chatgpt懂的很多, 但是很难一次到位, 目前看只能多加引导, 比如把复杂的任务拆分一个个小任务.  

## 细节  
[batch rename files on windows](https://github.com/zzblydia/myBlog/tree/master/windows/batch_rename)  