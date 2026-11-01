# MyTelegramBot

自用的 Telegram 机器人:查询 Singtel/t-sim 套餐余量并推送给管理员。
**使用说明、项目结构、脚本功能与业务逻辑见 `README.md`**,本文件只写改代码时必须遵守的约束。

## 硬约束

1. **分层单向**:`main.py → bot/ → business/`;`business/` 不得 import `telegram`、不得发消息、不得出现 `chat_id`。
2. **查询只返回文本**:`business/singtel.py: query_singtel_data(order_id) -> str` 内部捕获所有异常,失败返回 `查询失败: <原因>`,不向上抛;三个发送点(server/schedule/client)各自只写一行发送代码,不允许各自 `try/except`。
3. **初始化只发生一次**:`init_logger.init_logging()` 与 `init.config.load_config()` 只允许在 `main._bootstrap()` 调用,且**日志先于配置**;其他模块用 `logging.getLogger(__name__)`,只接收传入的 `config`。
4. **配置来源唯一**:固定 `config/config.json`,不回退 `config.example.json`;`config.example.json` 只放占位值,真实 `bot_token` 不得写入任何被跟踪文件。
5. **依赖带 extras**:`python-telegram-bot[job-queue]`,否则 `app.job_queue` 为 `None`;依赖变更同步 `requirements.txt`。
6. **日志必须脱敏**:任何日志中不得出现 bot token 明文。`init/logger.py` 的 `_RedactingFormatter` 会把 `bot<id>:<token>` 替换为 `bot<redacted>`,该 formatter 不可移除;新增日志代码也不得绕过它直接写文件/控制台。日志文件使用 `TimedRotatingFileHandler`(按天轮转、保留 14 份),不要改回普通 `FileHandler`,否则文件数无上限。
7. **Python 3.10 兼容**:GitHub Actions 使用 3.10,不使用 3.11+ 语法。

## 目录与职责

| 路径 | 职责 |
|---|---|
| `main.py` | 入口:日志/配置初始化、`bot_token` 校验、按 `run_mode` 分派 |
| `bot/server.py` | `Application` 构建、单一 handler 注册、私聊/群聊分派、`_respond_admin_query` |
| `bot/schedule.py` | `register_daily_job`(含 job_queue 缺失检查)、`scheduled_query` |
| `bot/client.py` | client 模式:一次性查询与发送 |
| `init/config.py` | `load_config()`,默认 `<项目根>/config/config.json` |
| `init/logger.py` | `init_logging()`,写 `<项目根>/logs/<时间戳>.log`,自动建目录 |
| `business/singtel.py` | 查询接口、签名、结果格式化;不含 telegram 依赖 |

`init/config.py` 与 `init/logger.py` 中的 `Path(__file__).parent.parent` 依赖 "`init/` 直接位于项目根" 这一前提,移动包层级时必须同步修改。

## 行为契约(改动前先确认不要破坏)

- 每日推送:**22:00 UTC = 06:00 SGT**,常量 `DAILY_PUSH_TIME`;
- 仅响应 `admin_user_id` 本人发送的 `/query singtel`;`admin_user_id` 为空时只记日志、不响应、不推送;
- 私聊与群聊都会响应,日志字段不同;两条路径共用 `_respond_admin_query`,注册的 handler 只有一个;
- client 模式查询一次即退出,不构建 `Application`;
- 日志 INFO 级、同时输出到文件与控制台;文件为 `logs/bot.log`,按天轮转保留 14 份;两者共用脱敏 formatter。

## 修改检查清单

1. 新增/移动/重命名模块 → 同步 `.github/workflows/daily_query.yml`、`README.md`、本文件的目录表;
2. 新增依赖 → 更新 `requirements.txt`,并保留 `[job-queue]` extra;
3. 配置字段变化 → 同步 README 配置表与 `main._validate_config()`;
4. 定时时间变化 → 只改 `bot/schedule.py: DAILY_PUSH_TIME`,同步 README;
5. docstring 只写"为什么/副作用/异常",不复述函数名与签名;行内注释只解释非显而易见的实现;
6. 提交前:`python -m compileall .`;`python -c "from business.singtel import query_singtel_data"` 应能在无 telegram 依赖时通过;确认日志中无 token 明文(搜索 `bot\d+:`)。
7. 涉及日志改动时,验证 `logs/` 下新文件里 `bot<id>:<token>` 已被替换为 `bot<redacted>`。

## 禁止事项

- 在业务模块内读取配置或初始化日志;
- 用 `sys.path` 注入解决跨包导入;
- 在 `business/` 内返回 telegram 对象或调用 `send_message`;
- 主动重构本次需求以外的代码。
