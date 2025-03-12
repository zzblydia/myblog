---
title:  "config github pages"
date:   2024-04-18 20:28:37 +0800
last_modified_at: 2024-04-20 21:00:00 +0800
categories: jekyll
---

# 记录一些搭建博客的想法和问题  

## todo
1.如何按标签和tag归类文章  
2.post的文章如何使用主题  
3.分页帖子数量  
4.博客正文太细长, 影响阅读体验, 如何按照屏幕自动适配?--->使用layout splash  

## do with minimal mistakes  
fork仓库后, 我做了哪些改动  
```
1. _config.yml  
2. _data/navigation.yml  
```

## three ways to use theme  

### gem theme  
适合自托管（Self-hosting）, 指的是你自己负责运行和托管 Jekyll 生成的网站  

### remote theme  
简单化引入, 下载远程主题的文件时不会覆盖本地文件, 从而依然可以定制化.  

### fork repo  
高度定制化.  