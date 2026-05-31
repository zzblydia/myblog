# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal blog hosted on GitHub Pages at `https://zzblydia.github.io/myblog`. 
Built with Jekyll using the [Minimal Mistakes](https://mmistakes.github.io/minimal-mistakes/)  
**remote theme** (`mmistakes/minimal-mistakes@4.28.0`, skin `air`).  
All site source lives under `docs/` — never run Jekyll commands from the repo root.

## Local Development

```bash
cd docs
bundle install            # first time, or after a Gemfile change
bundle exec jekyll serve  # http://localhost:4000/myblog
```

- `baseurl: /myblog`, so local URLs include the `/myblog` prefix.
- `_config.yml` is **not** hot-reloaded — restart the server after editing it.
- `docs/_site/` is Jekyll's build output (gitignored, regenerated on serve/build).
- `Gemfile` pins Jekyll via the `github-pages` gem to keep parity with GitHub Pages. `tzinfo-data` is included for Windows.

## Branch Structure

- `githubpages` — working branch; **GitHub Pages deploys from this branch's `docs/` folder**.
- `master` — repository default branch (origin/HEAD). PRs usually target this.

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

Post defaults (`_config.yml`): `layout: single`, `author_profile: false`, `toc: true` + `toc_sticky: true`, `comments: true`, `share: false`, `related: true`, and a default `header.overlay_image` (`/assets/images/sea_blue.jpg`).  
Permalink is `/:categories/:title/`; pagination shows 20 posts/page.  

## Theme Customization (the parts that need reading multiple files)

Since the theme is remote, customizations are layered on top via override files:

- `docs/assets/css/main.scss` — custom SCSS: `$max-width: 1500px`, post-page sidebar width fix, breadcrumb left-alignment.
- `docs/_includes/head/custom.html` — dark-mode styles + anti-flash-of-unstyled-content script (uses a `data-theme` attribute).
- `docs/_includes/footer/custom.html` — the dark-mode toggle button.
- `docs/_data/navigation.yml` — top nav (分类 / 标签 / 归档 / 关于).
- `docs/_pages/` — static archive pages (category / tag / year) + about. Archives are the GitHub-Pages-compatible Liquid type, so these pages must exist or breadcrumbs break.
- `docs/index.html` — site entry / home (header overlay `home.jpg`).

Enabled features in `_config.yml`: `enable_copy_code_button`, `breadcrumbs`, lunr `search`, and **giscus** comments (`comments.provider: giscus`, GitHub-login based, follows the color scheme).

## Plugins

`jekyll-paginate`, `jekyll-sitemap`, `jekyll-gist`, `jekyll-feed`, `jekyll-include-cache`.

## Privacy & Data Handling

`./docs/_posts` contains private/personal content.  
DO NOT read, transmit, upload, or reference its contents to any external service, API, or internet endpoint unless explicitly instructed in the current session.  
Working with the theme, layout, or config does not require reading post bodies.  

## 约束

处理 `mmistakes/minimal-mistakes` 主题相关问题时,请以本仓库使用的版本号(`4.28.0`)及官方最新资料为准,确保回答准确。
