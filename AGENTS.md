# AGENTS.md

This file provides guidance to agent when working with code in this repository.

## Overview

Personal blog hosted on GitHub Pages at `https://zzblydia.github.io/myblog`. 
Built with Jekyll using the [Minimal Mistakes](https://mmistakes.github.io/minimal-mistakes/)  
**remote theme** (`mmistakes/minimal-mistakes@4.28.0`, skin `air`).  
All site source lives under `docs/` — never run Jekyll commands from the repo root.

## Local Development

```bash
cd docs
bundle install          # first time or after Gemfile change
bundle exec jekyll serve  # http://localhost:4000/myblog
```

All site source lives under `docs/` — never run jekyll commands from repo root.

## Architecture

- GitHub Pages deploys from `githubpages` branch, `docs/` folder
- Remote theme: `mmistakes/minimal-mistakes@4.28.0` (skin: `air`) — custom overrides live in `docs/_includes/`
- Custom CSS: `docs/assets/css/main.scss` (overrides `$max-width: 1500px`, sidebar width fix, breadcrumb alignment)
- Dark mode: implemented via `docs/_includes/head/custom.html` and `docs/_includes/footer/custom.html` (`data-theme` attribute)
- `baseurl: /myblog` — local URLs include this prefix
- `_config.yml` changes require **server restart** (not hot-reloaded)
- `Gemfile` uses `github-pages` gem (pins Jekyll version for GitHub Pages compatibility)
- Windows needs `tzinfo-data` gem (already in Gemfile)
- `docs/_site/` is the Jekyll build output — gitignored, generated on `jekyll serve` or `jekyll build`

## Adding Posts

Path: `docs/_posts/<category>/YYYY-MM-DD-title.md`.  
Existing category dirs: `blog`, `c-cpp`, `life`, `linux`, `python`, `windows`, `work`.  

Required front matter:

```yaml
---
title:  "Post Title"
date:   2025-01-01 00:00:00 +0800
last_modified_at: 2025-01-01 00:00:00 +0800
categories: <category>
tags: <tag>
---
```

- Permalink: `/:categories/:title/`
- Paginate: 20 posts per page

## Key Files

- `docs/_config.yml` — site config, theme, plugins, defaults, comments (giscus)
- `docs/_data/navigation.yml` — top nav (分类, 标签, 归档, 关于)
- `docs/_pages/` — static archive pages
- `docs/index.html` — site entry
- `docs/assets/css/main.scss` — custom SCSS (max-width, sidebar, breadcrumb)
- `docs/_includes/head/custom.html` — dark mode styles + anti-flash script
- `docs/_includes/footer/custom.html` — dark mode toggle button

## Plugins

`jekyll-paginate`, `jekyll-sitemap`, `jekyll-gist`, `jekyll-feed`, `jekyll-include-cache`.

## Privacy

`./docs/_posts` contains private/personal content.  
DO NOT read, transmit, upload, or reference its contents to any external service, API, or internet endpoint unless explicitly instructed in the current session.  
Working with the theme, layout, or config does not require reading post bodies.  

## 约束

处理 `mmistakes/minimal-mistakes` 主题相关问题时,请以本仓库使用的版本号(`4.28.0`)及官方最新资料为准,确保回答准确。
