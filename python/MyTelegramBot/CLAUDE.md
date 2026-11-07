# MyTelegramBot

自用的 Telegram 机器人:查询 Singtel/t-sim 套餐余量推送给管理员,并把每日 60 秒新闻发布到指定频道。
**使用说明、项目结构、脚本功能与业务逻辑见 `README.md`**,本文件只写改代码时必须遵守的约束。

## 硬约束

1. **分层单向**:`main.py → bot/ → business/`;`business/` 不得 import `telegram`、不得发消息、不得出现 `chat_id`。
2. **查询只返回文本**:`business/singtel.py: query_singtel_data(order_id) -> str` 内部捕获所有异常,失败返回 `查询失败: <原因>`,不向上抛;三个发送点(server/schedule/client)各自只写一行发送代码,不允许各自 `try/except`。`business/news.py: fetch_daily_news() -> DailyNews | None` 同样不抛异常,失败返回 `None`,由调用方决定不发送并返回非 0 退出码。
3. **初始化只发生一次**:`init_logger.init_logging()` 与 `init.config.load_config()` 只允许在 `main._bootstrap()` 调用,且**日志先于配置**;其他模块用 `logging.getLogger(__name__)`,只接收传入的 `config`。
4. **配置来源唯一**:固定 `config/config.json`,不回退 `config.example.json`;`config.example.json` 只放占位值,真实 `bot_token` 不得写入任何被跟踪文件。
5. **依赖带 extras**:`python-telegram-bot[job-queue]`,否则 `app.job_queue` 为 `None`;依赖变更同步 `requirements.txt`。
6. **日志必须脱敏**:任何日志中不得出现 bot token 明文。`init/logger.py` 的 `_RedactingFormatter` 会把 `bot<id>:<token>` 替换为 `bot<redacted>`,该 formatter 不可移除;新增日志代码也不得绕过它直接写文件/控制台。日志文件使用 `TimedRotatingFileHandler`(按天轮转、保留 14 份),不要改回普通 `FileHandler`,否则文件数无上限。
7. **Python 3.10 兼容**:GitHub Actions 使用 3.10,不使用 3.11+ 语法。
8. **3HK 凭证只由调用方传入**:`business/three_hk.py` 不读取配置文件、不打印邮箱/密码/cookie/请求体/响应体;凭证由 `bot/client.py` 从 `config/config.json` 读取后传参。GitHub Actions 中只允许通过 Secrets `EMAIL` / `DIY_PASS` 注入生成的 `config.json`,不得硬编码到任何被跟踪文件、日志或第三方接口。

## 目录与职责

| 路径 | 职责 |
|---|---|
| `main.py` | 入口:日志/配置初始化、`bot_token` 校验、按 `run_mode` 分派 |
| `bot/server.py` | `Application` 构建、单一 handler 注册、频道/私聊/群聊分派、`_respond_admin_query`、`_log_channel_post` |
| `bot/schedule.py` | `register_daily_job`(含 job_queue 缺失检查)、`scheduled_query` |
| `bot/client.py` | client 模式一次性任务:`client_task=singtel` 发管理员、`news` 发频道、`3hk` 发管理员、`phone` 合并 Singtel + 3HK 后发管理员 |
| `init/config.py` | `load_config()`,默认 `<项目根>/config/config.json` |
| `init/logger.py` | `init_logging()`,写 `<项目根>/logs/<时间戳>.log`,自动建目录 |
| `business/singtel.py` | 套餐查询接口、签名、结果格式化;不含 telegram 依赖 |
| `business/three_hk.py` | 3HK DIY 余额/到期时间查询;凭证由调用方传入;不含 telegram 依赖;由 `client_task=3hk` / `phone` 调用 |
| `business/news.py` | 60s 新闻接口、文本格式化、海报下载;不含 telegram 依赖 |

`init/config.py` 与 `init/logger.py` 中的 `Path(__file__).parent.parent` 依赖 "`init/` 直接位于项目根" 这一前提,移动包层级时必须同步修改。

## 行为契约(改动前先确认不要破坏)

- 每日套餐推送:**22:00 UTC = 06:00 SGT**,常量 `DAILY_PUSH_TIME`(server)/ `daily_query.yml` 的 cron(client);
- 每日新闻推送:**23:00 UTC = 07:00 SGT**,只由 `.github/workflows/daily_news.yml` 触发;
- 仅响应 `admin_user_id` 本人发送的 `/query singtel`;`admin_user_id` 为空时只记日志、不响应、不推送;
- 私聊与群聊都会响应,日志字段不同;两条路径共用 `_respond_admin_query`,注册的 handler 只有一个;
- 频道帖子(`channel_post`)只由 `_log_channel_post` 记录 `channel_id` / 标题,**永不回复**;该接口用于获取私有频道数字 ID,永久保留;
- client 模式执行一次即退出,不构建 `Application`;任务由 `config.client_task` 决定,缺省 `singtel`,非法值启动即失败;`news` 缺 `news_channel_id`、`singtel` 缺 `order_id` 或 `admin_user_id`、`3hk` 缺 `email` / `pass` / `admin_user_id` 时启动即失败;`phone` 缺 `order_id` 或 `admin_user_id` 时启动即失败,`email` / `pass` 缺失只跳过 3HK;client 任务发送侧 `TelegramError` 统一在任务内收口并返回退出码 1(不回抛 traceback);
- `news_channel_id` 支持 `@username` / `t.me/username` / `-100` 数字 ID,`t.me/+` 邀请链接必须拒绝;
- 新闻接口固定「主用 `60s.okbaike.com` → 备用 `60s.zellon.top`」顺序,主用失败必须自动切备用;调试地址(60s.viki.moe)以注释形式保留,仅本地调试,不得用于生产请求;
- news 正文使用 HTML(`parse_mode=HTML`)+ emoji,动态内容必须 `html.escape`;标题/日期/农历顺序固定为「频道标题 → 日期星期 → 农历」,不展示原文链接;
- 配图统一走 `business.news.get_news_image_url()`,当前返回空串(60s 海报与正文重复);恢复配图后,正文解析后 ≤1000 字符时作为图注与图片合并为一条,超长或图片失败时退回「图片 + 文字」两条;
- 日志 INFO 级、同时输出到文件与控制台;文件为 `logs/bot.log`,按天轮转保留 14 份;两者共用脱敏 formatter;
- 3HK DIY 查询只返回文本,失败返回 `查询失败: <原因>`;余额接口失败仍返回到期时间;不做自动重试,`406` 不自动 `forceLogin`;凭证由调用方传入,模块不读配置、不记录邮箱/密码/cookie/请求体/响应体;
- `phone` 固定「先 Singtel、后 3HK」顺序执行;只展示成功结果,失败段显示「任务失败」;任一查询失败或 Telegram 发送失败返回退出码 1;`email` / `pass` 缺失时跳过 3HK 且不视为失败;`daily_query.yml` 使用 `client_task=phone`。

## client 任务实现要点

### 3HK(`client_task=3hk`)

1. `main._validate_config()`:校验 `email` / `pass` / `admin_user_id`,任一缺失直接退出码 1;
2. `bot/client.run_client()`:显式分派 `3hk` 到 `_run_three_hk()`,不能落到缺省的 singtel 分支;
3. `_run_three_hk()`:从 `config` 读取凭证并调用 `business.three_hk.query_3hk_data(email, pass)`;
4. 查询结果原样通过 `Bot.send_message()` 发给 `admin_user_id`;只有 Telegram 发送失败时返回退出码 1。

### 手机卡合并查询(`client_task=phone`)

1. `main._validate_config()`:要求 `order_id` / `admin_user_id`;`email` / `pass` 缺失只记 warning,不阻止启动;
2. `bot/client.run_client()`:显式分派 `phone` 到 `_run_phone()`;
3. `_run_phone()`:先调用 `query_singtel_data(order_id)`,凭证完整时再调用 `query_3hk_data(email, pass)`;
4. 合并规则:成功结果保留原标题(`Singtel` / `3HK DIY`),失败段只显示「任务失败」,两段之间空一行;
5. 发送:通过 `Bot.send_message()` 发给 `admin_user_id`;任一查询失败或发送失败返回退出码 1,便于 Actions 报警;
6. `.github/workflows/daily_query.yml` 使用 `client_task=phone`,并通过 Secrets `EMAIL` / `DIY_PASS` 生成 `config.json`。

## 修改检查清单

1. 新增/移动/重命名模块 → 同步 `.github/workflows/daily_query.yml`、`.github/workflows/daily_news.yml`、`README.md`、本文件的目录表;
2. 新增依赖 → 更新 `requirements.txt`,并保留 `[job-queue]` extra;
3. 配置字段变化 → 同步 README 配置表与 `main._validate_config()`;
4. 定时时间变化 → server 改 `bot/schedule.py: DAILY_PUSH_TIME`,client 改对应 workflow 的 cron,并同步 README;
5. docstring 只写"为什么/副作用/异常",不复述函数名与签名;行内注释只解释非显而易见的实现;
6. 提交前:`python -m compileall .`;`python -c "from business.singtel import query_singtel_data"`、`python -c "from business.news import fetch_daily_news"` 与 `python -c "from business.three_hk import query_3hk_data"` 应能在无 telegram 依赖时通过;确认日志中无 token 明文(搜索 `bot\d+:`)。
7. 涉及日志改动时,验证 `logs/` 下新文件里 `bot<id>:<token>` 已被替换为 `bot<redacted>`;同时确认 3HK 相关日志中无邮箱、密码、cookie、请求体、响应体。

## 禁止事项

- 在业务模块内读取配置或初始化日志;
- 用 `sys.path` 注入解决跨包导入;
- 在 `business/` 内返回 telegram 对象或调用 `send_message`;
- 主动重构本次需求以外的代码。
