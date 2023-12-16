set name=WLAN
set ipaddress=192.168.100.60
set mask=255.255.255.0
set gateway=192.168.100.171

netsh -c interface ip set address name="%name%" source=static addr=%ipaddress% mask=%mask% gateway=%gateway% gwmetric=0
netsh interface ip set dns name="%name%" source=static addr=%gateway% register=primary

pause