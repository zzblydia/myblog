# AGENTS.md

## Commands

```bash
cd docs
bundle install          # first time or after Gemfile change
bundle exec jekyll serve  # local dev at http://localhost:4000/myblog
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

- Path: `docs/_posts/<category>/YYYY-MM-DD-title.md`
- Required front matter: `title`, `date` (+0800), `last_modified_at`, `categories`, `tags`
- Default layout: `single` with `author_profile: false`, `toc: true`, `toc_sticky: true`, `header.overlay_image`
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

## Privacy

`./docs/_posts` contains private content. Do not transmit or upload post contents externally.

## background
我使用github pages+ jekyll + mimimal mistakes theme搭建我的个人博客.  
我希望将精力集中到博客文章本身,所以我是用了remote theme这种形式.  

## 约束
在处理主题mmistakes/minimal-mistakes的有关问题时,请参照我使用的版本号以及官方最新的资料,以保证回答的准确性.
