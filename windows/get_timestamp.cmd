@echo off
rem --------------------------------------------------------------
rem 方法一
rem date /t
rem 2023/12/16 周六
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do (
  set year=%%a
  set month=%%b
  set day=%%c
)
rem echo date:%year%%month%%day%

rem time
rem 20:39:07.71
for /f "tokens=1-4 delims=:." %%a in ("%time%") do (
  set hour=%%a
  set minute=%%b
  set second=%%c
  set millisecond=%%d
)
rem echo time:%hour%%minute%%second%_%millisecond%

set timestamp=%year%%month%%day%_%hour%%minute%%second%
echo timestamp:%timestamp%

rem --------------------------------------------------------------
rem 方法二
rem time 0到11点时小时数值前有空格
echo timestamp_simple:%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%

if %time:~0,2% LEQ 9 (echo timestamp_simple:%date:~0,4%%date:~5,2%%date:~8,2%_0%time:~1,1%%time:~3,2%%time:~6,2%) else (echo timestamp_simple:%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%)

pause