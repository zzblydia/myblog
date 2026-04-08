# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a personal blog hosted on GitHub Pages at `https://zzblydia.github.io/myblog`. It uses Jekyll with the [Minimal Mistakes](https://mmistakes.github.io/minimal-mistakes/) remote theme (`mmistakes/minimal-mistakes@4.27.0`). All site source lives under `docs/`.

## Local Development

```bash
cd docs
bundle install
bundle exec jekyll serve
```

The site is served locally at `http://localhost:4000/myblog`.

## Branch Structure

- `githubpages` — working branch; GitHub Pages deploys from this branch's `docs/` folder
- `main` — main branch

## Adding Posts

Posts go in `docs/_posts/<category>/YYYY-MM-DD-title.md`. Required front matter:

```yaml
---
title:  "Post Title"
date:   2025-01-01 00:00:00 +0800
last_modified_at: 2025-01-01 00:00:00 +0800
categories: <category>
tag: <tag>
---
```

The default layout for posts is `splash` with `author_profile: true` (set in `_config.yml` defaults). Posts are organized by topic under `docs/_posts/` subdirectories (c&&cpp, debian, git, jekyll, linux, python, windows, work, life, etc.).

## Key Configuration Files

- `docs/_config.yml` — site-wide settings, theme, plugins, permalink structure (`/:categories/:title/`), and post defaults
- `docs/_data/navigation.yml` — top navigation links (Categories, Tags, About)
- `docs/_pages/` — static archive pages for categories, tags, and year

## Plugins

`jekyll-paginate`, `jekyll-sitemap`, `jekyll-gist`, `jekyll-feed`, `jekyll-include-cache`

## Privacy & Data Handling

The following directories contain private/sensitive data.
DO NOT read, transmit, upload, or reference their contents to any external service, API, or internet endpoint:

- `./docs/_posts`

When working in this project, treat these paths as off-limits unless I explicitly instruct otherwise in the current session.
