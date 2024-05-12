rem 批量重命名文件

rem 背景
rem 下载的电视剧的名称不符合plex的搜刮要求, 通过批量重命名修改.
rem old name format: [晨曦制作&老M][艾斯奥特曼][xx][未来的艾斯是你!][中日双字幕][BDrip][HEVC Main10P FLAC MKV].mkv
rem new name format: 艾斯奥特曼__xx.mkv

@echo off
set "target_dir=E:\plex\dianshiju\aisi\"
for %%F in ("%target_dir%\*.mkv") do (
    for /F "tokens=2,3 delims=[]" %%G in ("%%~nxF") do (
        ren "%%F" "%%G_%%H.mkv"
    )
)

pause