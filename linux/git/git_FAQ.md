# some notes

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