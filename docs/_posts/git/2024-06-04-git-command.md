---
title:  "about git"
date:   2024-06-04 04:20:00 +0800
last_modified_at: 2024-06-04 06:27:00 +0800
categories: git
tags: git
---

# 关于git的认知过程  

## find git  
我是大概2022年左右接触`git`的, 在此之前都是使用的`svn`.  
当时项目大版本切换要求所有新代码都在git仓库管理,我也有机会使用到了git.  
使用之后感觉发现了新世界,在家使用`svn`的时候我都是本地搭建svn服务器,在公司协同编辑的时候还要等同事使用完解锁我才能继续编辑.而`git`可以有本地仓库,让我在本地也能进行版本管理.  


## install and environment  
在windows环境下我一般安装[git](https://git-scm.com/)和界面化工具[tortoisegit](https://tortoisegit.org/)  
 - git shell 在windows下方便地执行一些linux命令
 - tortoisegit 管理网络/密钥/查看修改文件列表/推送到远端

## git commands
有了大模型以后其实很方便了, 代码想做什么操作或者达到什么样的效果, 直接问ai就可以了, 所以如下命令的总结完全是因为自己随想随写,而不是系统的学习git命令.    

`git`仓库, 按照理解一般有三个:
 - 远端公共仓库(upstream)
 - 远端个人仓库(origin)
 - 本端个人仓库(local)  
 操作顺序一般是upstream fork 到 origin, origin 克隆到local.
 local修改后push到origin, 再merge到upstream.

### git clone
```
直接克隆
git clone https://github.com/warmcat/libwebsockets.git

指定目标文件夹名称
git clone https://github.com/warmcat/libwebsockets.git libwebsocket_official

按分支或者tag克隆
git clone -b v4.5-stable https://github.com/warmcat/libwebsockets.git
git clone -b v4.3.3 https://github.com/warmcat/libwebsockets.git

限定深度(倒数提交记录数), 比如只用来编译, 不关心提交历史
git clone -b main --depth=1 https://github.com/warmcat/libwebsockets.git
```

### git remote
```
显示远端公共仓库或者远端个人仓库地址
git remote -v

添加远端公共仓库
git remote add upstream_name https://github.com/warmcat/libwebsockets.git

获取远端公共仓库的所有分支
git fetch upstream_name
```

### git reset
```
舍弃本地修改, 重置当前分支, 重置提交进度与远程某个分支相同
git reset --hard upstream/main
```

### git checkout/switch
```
切换分支
git checkout branch_name
git switch branch_name

切换并创建新分支
git checkout -b new_branch_name upstream/main
git switch -c new_branch_name upstream/main
```

### git branch
```
删除本地分支
git branch -D branch_name

重命名本地分支
git branch -m old_branch_name new_branch_name
```

### git commit
```
修改最后一次提交记录
git commit --amend

提交本地修改
git commit -m "message
```

### git rebase
```
修改倒数历史3条记录
git rebase -i HEAD~3

保存本地修改记录并更新代码到与远端公共仓库相同
git rebase upstream/main
```

### git cherry
```
摘取某次提交到当前分支
git cherry pick commit_hash
```

## git practice 

### 1. sync upstream code with merge  
```
# 添加上游仓库
git remote add upstream https://github.com/originalowner/originalrepository.git

# 验证上游仓库是否添加成功
git remote -v

# 从上游仓库获取最新的更改
git fetch upstream

# 切换到主分支
git checkout main

# 合并上游仓库的更改
git merge upstream/main

# 将合并后的更改推送到您的个人仓库
git push origin main
```

### 2. sync upstream code with rebase  
**<font color="red">这种方式同步上游代码能避免提交日志中有类似以下无效信息, 且能把个人区别于上游的提交放在日志的最新</font>**  
`Merge branch 'xxx' of https://github.com/xxx/yyy into xxx`  

```
# 添加上游仓库
git remote add upstream https://github.com/originalowner/originalrepository.git

# 验证上游仓库是否添加成功
git remote -v

# 从上游仓库获取最新的更改
git fetch upstream

# 切换到主分支
git checkout main

# 使用 rebase 将您的更改应用到上游仓库的最新提交之上
git rebase upstream/main

# 将合并后的更改推送到您的个人仓库
git push origin main
```