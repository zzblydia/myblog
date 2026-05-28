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
- Remote theme: `mmistakes/minimal-mistakes@4.27.0` — custom overrides live in `docs/_includes/`
- `baseurl: /myblog` — local URLs include this prefix
- `_config.yml` changes require **server restart** (not hot-reloaded)
- `Gemfile` uses `github-pages` gem (pins Jekyll version for GitHub Pages compatibility)
- Windows needs `tzinfo-data` gem (already in Gemfile)
- `docs/_site/` is the Jekyll build output — gitignored, generated on `jekyll serve` or `jekyll build`

## Adding Posts

- Path: `docs/_posts/<category>/YYYY-MM-DD-title.md`
- Required front matter: `title`, `date` (+0800), `last_modified_at`, `categories`, `tag`
- Default layout: `single` with `author_profile: true`, `toc: true`, `toc_sticky: true`
- Permalink: `/:categories/:title/`
- Paginate: 20 posts per page

## Key Files

- `docs/_config.yml` — site config, theme, plugins, defaults
- `docs/_data/navigation.yml` — top nav (分类, 标签, 关于)
- `docs/_pages/` — static archive pages
- `docs/index.html` — site entry

## Privacy

`./docs/_posts` contains private content. Do not transmit or upload post contents externally.

## background
我使用github pages+ jekyll + mimimal mistakes theme搭建我的个人博客.
我希望将精力集中到博客文章本身,所以我是用了remote theme这种形式.
现在我对使用这个主题的一些疑问向你请教,请保证你的回答基于mmistakes/minimal-mistakes@4.27.0及以上
