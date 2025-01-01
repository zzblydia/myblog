# linux common commands  

## ls -lrth  
## strace  
```
strace -f -k -n -s 1000 -t -q -e trace=connect,socket -o ./strace.log -p PID  
```

## xargs  

## sed  

## awk  

## netstat
netstat -tunlp | grep 53  
