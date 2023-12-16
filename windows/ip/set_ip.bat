@echo off
mode con: cols=60 lines=25
title 网卡配置 by：Jack.liu
color 04
 
  
:hom
cls
echo.
echo -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
echo             〓〓〓一键配置网卡IP地址v3〓〓〓
echo.   
echo       您现在访问的用户是　%userdomain% \ %username%   
echo       现在的时间　　%date% %time% 
echo.      
echo.
echo.                  1  - 静态IP
echo.                  2  - DHCP分配
echo.                  3  - 自定义配置
echo.                  0  - 退出
echo.        本脚本作者：Jack.Liu  网站：xlsys.cn
echo.-----------------------------------------------------------
echo.               请以管理员身份运行本脚本
echo.
echo.
set input=
set /p input=请选择【输入序号,然后回车】:
if /i '%input%'=='1' goto :STATIC_IP
if /i '%input%'=='2' goto :DHCP_IP
if /i '%input%'=='3' goto :STATIC_CONFIG
if /i '%input%'=='0' goto :Exit
cls
echo.
echo.
echo.
echo   未输入正确的序号，任意键返回上层菜单
echo.
pause
goto hom
 
 
 
:STATIC_IP
cls
echo.
echo -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
echo               〓〓〓静态IP模式〓〓〓
echo.   
echo       您现在访问的用户是　%userdomain% \ %username%   
echo       现在的时间　　%date% %time% 
echo.      
echo.
echo.                  1  - 公司
echo.                  2  - 宿舍
echo.                  3  - 家里
echo.                  0  - 退出
echo.        本脚本作者：Jack.Liu  网站：xlsys.cn
echo.-----------------------------------------------------------
set input=
set /p input=请选择【输入序号,然后回车】:
if /i '%input%'=='1'  goto :STATIC_IP_COMPANY
if /i '%input%'=='2'  goto :STATIC_IP_DORM
if /i '%input%'=='3'  goto :STATIC_IP_HOME
if /i '%input%'=='0'  goto :Exit
cls
echo.
echo.
echo.
echo   未输入正确的序号，任意键返回上层菜单
echo.
pause
goto hom
  
REM 需要设置的网络，一般为"本地连接"或者"无线网络连接"
set name=以太网
REM 设置静态IP
:STATIC_IP_CONFIG
netsh -c interface ip set address name="%name%" source=static addr=%ipaddress% mask=%mask% gateway=%gateway% gwmetric=0
goto :PRINT_CONFIG
REM netsh -c interface ip add address name="%name%" addr=%ipaddress2% mask=%mask2% gateway=%gateway2% gwmetric=1
  
REM 设置动态IP
:DHCP_IP
echo 正在进行动态IP设置，请稍等...
netsh interface ip set address name=%name% source=dhcp
goto :Exit
  
REM 打印设定内容
:PRINT_CONFIG
echo. IP地址 = %ipaddress% .完成设置
echo. 子掩码 = %mask% .完成设置
echo. 网关 = %gateway% .完成设置
goto :DNS_CONFIG
  
REM 配置为公司IP
:STATIC_IP_COMPANY
echo.
set /p CompanyIP=选择公司公司楼层, 1:29楼,2:32楼 :
if /i %CompanyIP%==1 goto :COMPANY_29
if /i %CompanyIP%==2 goto :COMPANY_32
  
REM #### 设置静态IP ####
:COMPANY_29
set ipaddress=192.168.10.222
set mask=255.255.255.0
set gateway=192.168.10.254
goto :STATIC_IP_CONFIG
  
:COMPANY_32
set ipaddress=10.50.200.200
set mask=255.255.255.0
set gateway=10.50.200.254
goto :STATIC_IP_CONFIG
  
REM 配置为宿舍IP
:STATIC_IP_DORM
set ipaddress=172.16.41.252
set mask=255.255.0.0
set gateway=172.16.0.1
goto :STATIC_IP_CONFIG
REM 配置为家里IP
:STATIC_IP_HOME
set ipaddress=172.16.41.252
set mask=255.255.0.0
set gateway=172.16.0.1
goto :STATIC_IP_CONFIG
:STATIC_CONFIG
echo.
set /p ipaddress=请输入指定的静态IP(例如:172.16.1.100):
set /p mask=请输入子网掩码(例如:255.255.0.0):
set /p gateway=请输入网关地址(例如:172.16.0.1):
goto :STATIC_IP_CONFIG
  
:DNS_CONFIG
echo.
set /p dnsconfig=指定DNS, 1:谷歌, 2:阿里, 3:114, 4:自动 :
if /i %dnsconfig%==1 goto :DNS_GOOGLE
if /i %dnsconfig%==2 goto :DNS_ALI
if /i %dnsconfig%==3 goto :DNS_114
if /i %dnsconfig%==4 goto :DNS_AUTO
  
REM 设定谷歌DNS
:DNS_GOOGLE
set dns1=8.8.4.4
set dns2=8.8.8.8
goto :DNS_SET
REM 设定阿里DNS
:DNS_ALI
set dns1=223.5.5.5
set dns2=223.6.6.6
goto :DNS_SET
REM 设定114DNS
:DNS_114
set dns1=114.114.115.115
set dns2=114.114.114.114
goto :DNS_SET
  
REM 设定自动获取DNS
:DNS_AUTO
netsh interface ip set dns name=%name% source=dhcp register=PRIMARY
netsh interface ip set wins name=%name% source=dhcp
  
REM DNS设置生效
:DNS_SET
netsh -c interface ip set dns name="%name%" static %dns1% >nul
netsh -c interface ip add dns name="%name%" addr=%dns2% index=2 >nul
echo. 首选DNS = %dns1% .完成设置
echo. 备用DNS = %dns2% .完成设置
REM 结束
:Exit
exit