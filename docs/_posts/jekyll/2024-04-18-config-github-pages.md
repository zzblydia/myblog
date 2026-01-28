---
title:  "learn github pages"
date:   2024-04-18 20:28:37 +0800
last_modified_at: 2025-03-13 01:33:00 +0800
categories: github
tag: github_pages
---

# 记录使用github pages搭建博客的认知过程  

## 背景
我想搭建自己的博客, 趁着自己还对代码有那么一点点热情, 输出一些体会和总结.  

同时又不想在搭建博客这件事上浪费太多时间, 而是集中精力到写博客这件事.  

经过一番探索看到了github pages, 我感觉符合我的预期:  

 - 不需要个人维护和费用 (即使有一天人不在了页面也会在吧)  
 - 内置jekyll 不需要额外生成站点

## github pages基础认知  

### 站点类型  
一类站点是个人或组织, 站点资源存储在仓库`username.github.io`, 访问url `username.github.io`  
一类是工程站点, 站点资源存储在project仓库, 可以是仓库的`根目录`或者`/docs`目录, 访问url `username.github.io/project_name`  

### 需要熟悉的软件和环境  
 - ruby  
 - jekyll  
 - gem  
 - bundle  
