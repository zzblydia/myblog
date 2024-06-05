---
title:  "git-commands"
date:   2024-06-04 04:20:00 +0800
last_modified_at: 2024-06-04 06:27:00 +0800
categories: git
tags: git
---

# some notes of git commands  

## git command 

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