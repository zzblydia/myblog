# some notes of gdb  

## attach  
gcc -g -o helloworld helloworld.c &&　./helloworld &  
ps -ef | grep helloworld  
gdb helloworld  
b main  
attach pid  

## handle  
handle SIGTERM nostop  
handle SIG36 nostop noprint  
handle SIG35 nostop noprint  

## command  
break function  
commend  
bt 20  
c  
end  
attach pid  

## temp variable  
set $tmp = 0  
set $tmp = $tmp + 1  

## watch  
watch/rwatch/awatch g_timesCount  
commend  
bt 20  
c  
end  

## break  
b function if (input para == 3)  
commend  
set $count = 0  
c  
end  
b file:line if ($count % 2 == 0)  
commend  
p $count  
end  

