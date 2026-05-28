# Personal Site  

## preview on Windows  
[Testing your GitHub Pages site locally with Jekyll](https://docs.github.com/zh/pages/setting-up-a-github-pages-site-with-jekyll/testing-your-github-pages-site-locally-with-jekyll)  

### Prerequisites
1. [Ruby+Devkit](https://rubyinstaller.org/downloads/)  
```
ruby -v  
gem -v  
gcc -v  
g++ -v  
make -v  
```

2. gem install jekyll  
```
jekyll -v  
```
3. gem install bundler  

### command  
```
cd docs  
bundle install  
bundle exec jekyll serve  
bundle exec jekyll serve --host 192.168.8.60
```

## changelog

### 2026-05-30 博客优化

- 远程主题升级 `4.27.0` → `4.28.0`
- 皮肤切换 `dirt` → `air`
- 启用代码复制按钮 `enable_copy_code_button: true`
- 启用站内搜索 `search: true`（lunr，零外部依赖）
- 启用面包屑导航 `breadcrumbs: true`
- 添加副标题 `subtitle: "详细真实但不一定有趣的折腾"`
- 导航栏新增"归档"入口
- 页面宽度优化 `$max-width: 1500px`（`docs/assets/css/main.scss`）
- 文章页去掉作者侧边栏，空白区域由正文填补
- 面包屑从居中改为与正文左对齐
- 隐藏文章底部社交分享按钮 `share: false`
- 启用 giscus 评论系统（GitHub 登录，自动跟随暗色模式）
- 首页添加 header overlay 配图 `home.png`
- 文章页默认 header overlay 配图 `sea_blue.png`

