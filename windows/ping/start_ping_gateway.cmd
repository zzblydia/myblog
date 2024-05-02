if %time:~0,2% LEQ 9 (
    set timestamp=%date:~0,4%%date:~5,2%%date:~8,2%_0%time:~1,1%%time:~3,2%%time:~6,2%
) else (
    set timestamp=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
)

cscript C:\vm\ping\ping.vbs 192.168.8.1 -t -l 1000 -w 5000 >>C:\vm\ping\pinglog\%timestamp%_ping_gateway.txt