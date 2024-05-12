rem 批量重命名文件

rem 背景
rem 下载的电视剧的名称不符合plex的搜刮要求, 通过批量重命名修改.
rem old name format: [晨曦制作&老M][艾斯奥特曼][xx][未来的艾斯是你!][中日双字幕][BDrip][HEVC Main10P FLAC MKV].mkv
rem new name format: 艾斯奥特曼__xx.mkv

rem 发现bug: old name 中含有!时脚本无法处理, 要想正确处理, 必须不适用 延迟变量扩展delayedexpansion
rem 正确方案见batch_rename_2.bat

@echo off

setlocal enabledelayedexpansion

set "folder_path=E:\plex\test\"

rem 遍历文件夹中的.mkv文件
for %%f in ("%folder_path%\*.mkv") do (
    rem 获取文件名
    set "file_name=%%~nxf"
	echo "!file_name!"
    
    rem 解析文件名中的第2和第3个[]里面的内容
    for /f "tokens=2,3 delims=[]" %%a in ("!file_name!") do (
        set "old_name=!folder_path!!file_name!"
        set "new_name=!folder_path!%%a_%%b."
        
        rem 打印重命名前后的文件名
        echo old_name "!old_name!" 
		echo new name "!new_name!"
        
        rem 使用ren命令重命名文件
        ren "!old_name!" "!new_name!"
    )
)

endlocal
pause