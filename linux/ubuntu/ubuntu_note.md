# some notes  

## FAQ
### 1. apt-get update error:  
```
apt-get update
命中:1 http://archive.ubuntu.com/ubuntu noble InRelease
获取:2 http://security.ubuntu.com/ubuntu noble-security InRelease [126 kB]
获取:3 http://archive.ubuntu.com/ubuntu noble-updates InRelease [126 kB]
获取:4 http://archive.ubuntu.com/ubuntu noble-backports InRelease [126 kB]
正在读取软件包列表... 完成
E: http://security.ubuntu.com/ubuntu/dists/noble-security/InRelease 的 Release 文件已经过期(已经过期了 1天 10小时 1分 17秒)。该仓库的更新将不会应用。
E: http://archive.ubuntu.com/ubuntu/dists/noble-updates/InRelease 的 Release 文件已经过期(已经过期了 1天 16小时 19分 8秒)。该仓库的更新将不会应用。
E: http://archive.ubuntu.com/ubuntu/dists/noble-backports/InRelease 的 Release 文件已经过期(已经过期了 1天 10小时 2分 33秒)。该仓库的更新将不会应用。
```

solution:**check and update system time**  

### 2. secureCRT change dir color  
1>cd ~
2>dircolors -p > .dircolors  
3>vi .dircolors  
4>"dir 01;34" ---> "dir 01;35"  
5>source .bashrc  

### 3. secureCRT change path color  
1>vi .bashrc  
2>env PS1  34 ---> 35  
3>source .bashrc  
