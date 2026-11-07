# MyTelegramBot

一个自用的 Telegram 机器人:查询 Singtel/t-sim 手机套餐余量推送给管理员,并在每天早晨把「60 秒读懂世界」新闻发布到指定频道。

支持两种运行方式:

- **server 模式**:进程常驻,实时响应管理员的查询指令,并在每天固定时间自动推送一次套餐余量;同时记录频道帖子里的频道 ID;
- **client 模式**:由外部定时器(本地 cron 或 GitHub Actions)触发,按 `client_task` 执行一次「查套餐」「发新闻」或「查手机卡(Singtel + 3HK)」,随即退出。

---

## 一、使用方法

### 1. 环境要求

| 场景 | Python 版本 | 说明 |
|---|---|---|
| 本地长期运行 | 3.13.x | 项目实际开发环境 |
| GitHub Actions | 3.10 | `python-telegram-bot` 要求 `>=3.10`,workflow 里写死 3.10 |

### 2. 安装依赖

```bash
cd python/MyTelegramBot
python -m venv .venv                       # 首次执行
.venv/bin/pip install -r requirements.txt  # 或用 PyCharm 包管理器装
```

`requirements.txt` 里的 `python-telegram-bot[job-queue]` **必须带 `[job-queue]`**。少了它,PTB 会把 `app.job_queue` 静默置为 `None`,启动时表现为:

```text
AttributeError: 'NoneType' object has no attribute 'run_daily'
```

### 3. 配置

配置文件固定为 `config/config.json`(已被 `.gitignore` 忽略),首次使用从模板复制:

```bash
mkdir -p config
cp config/config.example.json config/config.json
```

然后填写以下字段:

| 字段 | 含义 | 说明 |
|---|---|---|
| `bot_token` | BotFather 发放的 token | 必填;仍是 `REPLACE_WITH_...` 时程序会拒绝启动 |
| `admin_user_id` | 管理员的 Telegram 用户 ID | server 模式为空时只记录消息、不响应指令;`client_task=singtel` / `3hk` / `phone` 时必填 |
| `order_id` | 订单号,查询接口的 `reference` 参数 | `client_task=singtel` / `phone` 时必填,否则启动即失败 |
| `news_channel_id` | 新闻推送目标频道 | 支持 `@username`、`https://t.me/username`、`-100` 开头的数字 ID;`client_task=news` 时必填 |
| `email` | 3HK DIY 登录邮箱 | `client_task=3hk` / `phone` 使用;本地放 `config/config.json`,Actions 中由 Secret 注入 |
| `pass` | 3HK DIY 登录密码 | `client_task=3hk` / `phone` 使用;本地放 `config/config.json`,Actions 中由 Secret 注入 |
| `run_mode` | `server` 或 `client` | 决定进程行为 |
| `client_task` | `singtel`、`news`、`3hk` 或 `phone` | 仅 client 模式生效;缺省为 `singtel`,老配置行为不变 |

示例(占位值,不能直接运行):

```json
{
    "bot_token"       : "REPLACE_WITH_BOT_TOKEN",
    "admin_user_id"   : "123456789",
    "order_id"        : "123456",
    "news_channel_id" : "@my_channel",
    "email"           : "REPLACE_WITH_3HK_EMAIL",
    "pass"            : "REPLACE_WITH_3HK_PASSWORD",
    "run_mode"        : "server",
    "client_task"     : "singtel"
}
```

> `config.example.json` 只用于复制,程序**不会**回退读取它。这样占位 token 不会被误当成有效配置跑起来。

### 4. 运行

```bash
# 长期在线(server 模式)
.venv/bin/python main.py

# 一次性任务(client 模式):先把 run_mode 改成 client,再按 client_task 执行
.venv/bin/python main.py
```

client 模式下任务由 `config.json` 的 `client_task` 决定,不需要命令行参数:

- `client_task = "singtel"`(缺省):查询套餐余量并发给 `admin_user_id`;
- `client_task = "news"`:拉取当日新闻并发布到 `news_channel_id`;
- `client_task = "3hk"`:只查询 3HK DIY 余额与到期时间并发给 `admin_user_id`;
- `client_task = "phone"`:先查 Singtel,再查 3HK,把成功结果合并成一条消息发给 `admin_user_id`;`email` / `pass` 缺失时自动跳过 3HK,只发 Singtel。

也可以直接在 PyCharm 里以 `main.py` 为脚本运行;注意 Working directory 必须是项目根目录 `python/MyTelegramBot`,否则 `bot/`、`init/`、`business/` 无法导入。

### 5. 机器人指令与频道 ID

| 指令 / 行为 | 发送者 | 行为 |
|---|---|---|
| `/query singtel` | 仅 `admin_user_id` 本人 | 立即查询并回复套餐名称、失效时间、用量 |
| 频道帖子 | 频道管理员(含 bot 自己) | 只记录 `channel_id` / 频道标题,不回复 |

其他人的消息、其他指令一律忽略;server 模式仍会记录消息日志。

**获取频道数字 ID**:把 bot 加进频道并设为**管理员**(否则 Telegram 不会下发频道帖子),server 模式下在频道里发一条消息,日志中会出现:

```text
Channel post - channel_id: -1001234567890, channel_title: xxx, username: xxx, ...
```

把 `-1001234567890` 填入 `news_channel_id` 即可。该日志接口永久保留,不要删除。公开频道也可以直接填 `@username`;`t.me/+xxxx` 形式的邀请链接无法被 Bot API 解析。

### 6. 日志

- 位置:`logs/bot.log`,当前日志始终叫这个名字,`tail -f logs/bot.log` 即可;
- 轮转:每天**本地时间 00:00** 自动切分为 `logs/bot.log.YYYYMMDD`,保留 14 份,超出的自动删除;进程重启不会新建文件,而是继续追加;
- 输出:同时写文件与**控制台(stderr)**,级别 INFO;GitHub Actions 里可直接在任务日志中看到输出;
- **token 脱敏**:`init/logger.py` 的 `_RedactingFormatter` 会把 `bot<id>:<token>` 形式的 URL 替换为 `bot<redacted>`,文件和**控制台**都不会出现 token;分享日志前仍建议先 `grep` 确认;
- 目录被 `.gitignore` 忽略,不会入库。

---

## 二、项目结构

```text
python/MyTelegramBot/
├── main.py                     # 入口:初始化日志/配置 → 校验 → 按 run_mode 分派
├── requirements.txt            # 依赖
├── config/
│   ├── config.json             # 本地真实配置(忽略)
│   └── config.example.json     # 模板(入库,保证 config/ 目录存在)
├── bot/                        # telegram 交互层
│   ├── server.py               # Application、handler、频道/私聊/群聊分派、命令响应
│   ├── client.py               # client 模式的一次性任务(singtel / news / 3hk / phone)
│   └── schedule.py             # 定时器注册 + 每日任务
├── init/                       # 基础设施层
│   ├── config.py               # load_config()
│   └── logger.py               # init_logging()
├── business/                   # 业务层
│   ├── singtel.py              # 套餐查询接口调用、签名、结果格式化
│   ├── three_hk.py             # 3HK DIY 余额/到期时间查询(client_task=3hk / phone)
│   └── news.py                 # 60s 新闻接口调用、文本格式化、海报下载
└── logs/                       # 运行时生成(忽略)
```

依赖方向严格单向,不存在循环导入:

```text
main.py ──> init.config / init.logger
   ├──> bot.client ──> business.singtel / business.news / business.three_hk
   └──> bot.server ──> bot.schedule ──> business.singtel
                  └──> business.singtel
```

约束:`business/` 不 import telegram、不知道 `chat_id`、不发消息。

---

## 三、脚本功能

### main.py

1. `init_logging()`:先初始化日志(必须在读配置之前,配置告警才能落盘);
2. `load_config()`:读 `config/config.json`,缺失时抛出带修复提示的错误;
3. 校验 `bot_token` 非空且不是占位值;client 模式额外校验 `client_task` 合法、`news` 必须有 `news_channel_id`、`singtel` 必须有 `order_id` 和 `admin_user_id`、`3hk` 必须有 `email` / `pass` / `admin_user_id`、`phone` 必须有 `order_id` 和 `admin_user_id`(`email` / `pass` 缺失时只跳过 3HK);
4. 按 `run_mode` 分派:`client` → `asyncio.run(run_client(config, task))` 并透传退出码,`server` → `run_server(config)`。

### server 模式(`bot/server.py` + `bot/schedule.py`)

- 构建 `Application`,配置写入 `bot_data["config"]`;
- 只注册**一个** `MessageHandler(filters.ALL, handle_message)`,内部按更新类型分派:
  - `channel_post`:`_log_channel_post()` 只记录 `channel_id` / 频道标题,用于获取私有频道 ID,不回复(永久保留);
  - `handle_private_message()`:记录 user_id / 昵称 / 内容;
  - `handle_group_message()`:额外记录 group_id / 群名;
  - 私聊与群聊都调用共用的 `_respond_admin_query()`,因此不会出现"同一消息被处理两次";
- `register_daily_job()` 注册每日任务;`job_queue` 为 `None`(缺 APScheduler)时直接报错退出,给出安装命令;
- `app.run_polling()` 阻塞运行。

### client 模式(`bot/client.py`)

- 不需要 `Application`,直接用 `async with Bot(...)` 发送消息;
- 任务由 `config.client_task` 决定,缺省 `singtel`:
  - `singtel`:查询一次套餐余量发给 `admin_user_id`;`order_id` / `admin_user_id` 缺失时启动即失败(退出码 1);
  - `news`:拉取新闻 → `get_chat()` 取频道标题 → 发送文字(超 4096 字符自动分片);配图由 `get_news_image_url()` 预留接口控制,当前返回空串不发图;获取或发送失败时退出码 1,让 Actions 变红;
  - `3hk`:用本地 `config.json` 的 `email` / `pass` 登录 3HK,查询余额与到期时间后发给 `admin_user_id`;`email` / `pass` / `admin_user_id` 缺失时启动即失败(退出码 1);
  - `phone`:按顺序先查 Singtel、再查 3HK,把成功结果用两段式合并成一条消息发给 `admin_user_id`;失败的查询段显示「任务失败」,并在发送后返回退出码 1;`email` / `pass` 缺失时跳过 3HK,只发 Singtel;`order_id` / `admin_user_id` 缺失时启动即失败;
- `news_channel_id` 支持 `@username`、`https://t.me/username`、`-100` 数字 ID;`t.me/+` 邀请链接会被拒绝并提示改用数字 ID。

---

## 四、业务逻辑

### 查询接口

```text
GET https://api.tsimtech.com/tsim/shopify/getGygPlanInfo?reference={order_id}
```

- 请求头模拟 Windows Chrome,并携带每次动态生成的 `TSIM-ACCOUNT` / `TSIM-NONCE` / `TSIM-TIMESTAMP` / `TSIM-SIGN`;
- 签名算法(HMAC-SHA256)在 `business/singtel.py` 中实现,无需手动维护;
- 超时 30 秒;请求 URL、参数、请求头、响应状态与响应体在 DEBUG 级别打印。

### 输出字段

对响应 `result[0]` 取以下字段,缺失则跳过该行:

| 字段 | 输出 |
|---|---|
| `channel_dataplan_name` | `套餐名称: <值>` |
| `expire_time` | `失效时间: <值>` |
| `data_usage` | `用量: <两位小数> M` |

### 3HK DIY 查询(`client_task=3hk` / `phone`)

`business/three_hk.py` 提供 3HK DIY 预付费卡的余额与到期时间查询。`client_task=3hk` 会单独发送 3HK 结果;`client_task=phone` 会把它和 Singtel 结果合并成一条消息。它不接入 server / schedule。

```python
from business.three_hk import query_3hk_data

# 凭证由调用方从 config/config.json 读取后传入
text = query_3hk_data(config["email"], config["pass"])
```

- 登录:`POST https://www.three.com.hk/ft-prepaid-pro/user/login/`;
- 资料:`GET .../user/getProfile`,取 `subscriptions[]` 中 `serviceType = "PREPAID"` 的订阅;
- 余额:`GET .../sim/{subscriptionId}/WalletBalances`,汇总 `carrierBillBalance` 为假的 `amount`;
- 到期时间:`subscription.subsEndDate`,统一格式化为 `YYYY-MM-DD HH:MM`;带时区的值转成香港时间;
- 套餐流量暂未实现,当前账号没有订购套餐;
- 余额接口失败但资料接口成功时,仍返回到期时间,余额显示 `查询失败`;
- 失败统一返回 `查询失败: <原因>`,不抛异常;
- 不做自动重试;遇到 `406` 不自动 `forceLogin`,避免把网页端登录踢下线;
- 凭证只从调用方传入,模块不读取配置文件,日志不记录邮箱、密码、cookie、请求体、响应体;
- 本地用 `client_task=3hk` 或 `phone`;GitHub Actions 中由 `phone` 任务调用,凭证来自 `EMAIL` / `DIY_PASS` Secrets,由 workflow 生成 `config.json`,不写入任何入库文件。

本地调试(两种方式都不会打印账号密码):

```bash
# 方式一:直接调用函数
.venv/bin/python -c 'import json; from business.three_hk import query_3hk_data; c=json.load(open("config/config.json", encoding="utf-8")); print(query_3hk_data(c["email"], c["pass"]))'

# 方式二:改好 config.json 后走 client 模式(结果发到 Telegram)
# client_task=3hk 只查 3HK;client_task=phone 合并 Singtel + 3HK
.venv/bin/python main.py
```

### 新闻接口

```text
主用: GET https://60s.okbaike.com/v2/60s?encoding=json
备用: GET https://60s.zellon.top/v2/60s?encoding=json
调试: GET https://60s.viki.moe/v2/60s?encoding=json   (仅本地测试,不参与生产)
```

- 主用失败(网络错误、非 2xx、`code != 200`、空列表)自动切换备用;两个都失败才返回 `None`;
- 调试地址以注释形式保存在 `business/news.py`,需要调试时临时把 `NEWS_URL` 指过去;
- 无需鉴权,单地址超时 15 秒;成功码是 `code == 200`(注意不是 singtel 接口的 `1`);
- 取 `data.news`(条目数组)、`data.date` / `day_of_week` / `lunar_date`、`data.tip`(微语)、`data.link`(原文)、`data.image`(当日海报);
- 用 `encoding=json` 而不是 `text`,是为了能校验业务码与空列表,避免把错误响应当新闻发出去;
- 发布内容:当前**只发文字**——60s 海报与正文内容完全重复,已暂时停发图片;
- 配图接口预留:`business.news.get_news_image_url(news)` 返回图片直链,空串表示不发图;后续换其他图源只改这个函数,客户端无需变动;
- 图片恢复后:正文解析后 ≤1000 字符时作为图注与图片合并为一条,否则退回「图片 + 文字」两条(文字超 4096 字符自动分片);
- 正文用 HTML(`parse_mode=HTML`)+ emoji 做视觉强调,所有动态内容经 `html.escape` 转义;Telegram 不支持文字颜色;
- 正文结构:`📢 频道标题` → `📅 2026年11月1日 星期日` → `🌙 农历 丙午年九月廿三` → 新闻列表(每条之间空一行)→ 微语;原文链接不展示;
- 频道标题由 `bot.get_chat()` 实时获取,不写入配置;取不到时该行留空,不影响发送。

### 异常处理

`query_singtel_data()` 对外**永不抛异常**:

- 网络错误、HTTP 非 2xx、`code != 1`、`result` 为空、无可解析字段,统一记录 `logger.exception` 后返回 `查询失败: <原因>`;
- 因此 server / schedule / client 三个发送点各自只有一行发送代码,不需要重复 `try/except`。

`fetch_daily_news()` 同样不抛异常,失败返回 `None`;`client_task=news` 时不发频道并以退出码 1 结束,便于 GitHub Actions 报警。

`query_3hk_data()` 同样不抛异常,失败返回 `查询失败: <原因>`;`client_task=3hk` 会把这个文本发给管理员,只有 Telegram 发送失败时才返回退出码 1。

`client_task=phone` 先执行 `query_singtel_data()`,再执行 `query_3hk_data()`;单条结果以 `查询失败` 开头时,该段只显示「任务失败」,成功段照常展示并合并发送。任一查询失败或 Telegram 发送失败时,进程返回退出码 1;`email` / `pass` 缺失时跳过 3HK,不视为失败。

### 定时与时区

- 套餐推送:每天 **06:00 SGT(UTC+8)= 22:00 UTC**;
  - 修改位置:`bot/schedule.py` 的 `DAILY_PUSH_TIME`(server 模式)、`.github/workflows/daily_query.yml` 的 cron(client 模式);
- 新闻推送:每天 **07:00 SGT(UTC+8)= 23:00 UTC**;
  - 修改位置:`.github/workflows/daily_news.yml` 的 cron;
- `tzinfo=timezone.utc` 必须保留,否则会按运行机器的本地时区解释。

### 已知限制

- `requests.get()` 是同步调用,在 async handler 中执行最长会阻塞事件循环 30 秒,期间 bot 不处理其他消息。当前未做线程池改造。
- 3HK DIY 接口是未公开的内部 API,字段与路径可能随前端版本变化;当前按前端 `0.68.0` 实现,失效时需同步更新 `platformVersion` 与字段解析。
- 3HK 查询未接入 server / schedule;GitHub Actions 中仅通过 `phone` 任务执行。接口是未公开的内部 API,若账号登录需要 OTP 或新设备验证,纯密码登录会失败。

---

## 五、GitHub Actions

两个独立工作流,互不影响:

| 工作流 | 触发时间 | 任务 | 需要的 Secrets |
|---|---|---|---|
| `.github/workflows/daily_query.yml` | 每天 22:00 UTC(06:00 SGT) | `client_task=phone` | `BOT_TOKEN`、`ADMIN_USER_ID`、`ORDER_ID`、`EMAIL`、`DIY_PASS` |
| `.github/workflows/daily_news.yml` | 每天 23:00 UTC(07:00 SGT) | `client_task=news` | `BOT_TOKEN`、`NEWS_CHANNEL_ID` |

`phone` 任务先查 Singtel、再查 3HK,把成功结果合并成一条消息发送;失败段显示「任务失败」并让 workflow 变红。`EMAIL` / `DIY_PASS` 未配置时会自动跳过 3HK,只发送 Singtel 结果。

- 两者都支持手动 `workflow_dispatch`;
- 步骤:安装 `requirements.txt` → 用 Secrets 生成 `config/config.json`(含各自的 `client_task`)→ `python main.py`;
- `daily_query.yml` 用 Python `json.dump` 生成配置,避免密码中的引号/反斜杠破坏 JSON;
- 由于 `config/` 里除模板外没有入库文件,workflow 直接写 `config/config.json` 即可,不需要 `mkdir`;
- GitHub Actions 的 cron 是 UTC,且实际触发常有 5～20 分钟延迟;仓库连续 60 天无提交时 schedule 会被自动暂停。

---

## 六、常见问题

| 现象 | 原因与处理 |
|---|---|
| `AttributeError: 'NoneType' object has no attribute 'run_daily'` | 缺 `[job-queue]`,执行 `pip install "python-telegram-bot[job-queue]"` |
| `配置文件不存在: .../config/config.json` | 未创建配置,按报错提示 `cp config/config.example.json config/config.json` |
| `bot_token 未配置或仍为占位值` | `config.json` 还是模板内容,填入真实 token |
| `ModuleNotFoundError: No module named 'bot'` | 用 `python main.py` 从项目根目录启动,或把 PyCharm 的 Working directory 设为项目根 |
| `client_task 非法` | `config.json` 里 `client_task` 只能是 `singtel` 或 `news` |
| `client_task=news 但 news_channel_id 未配置` | 填入频道 `@username` 或 `-100` 数字 ID |
| `client_task=singtel 但 order_id 未配置` | 填入订单号(查询接口的 `reference` 参数) |
| `client_task=singtel 但 admin_user_id 未配置` | 填入管理员的数字用户 ID |
| `news_channel_id 无法解析` | `t.me/+xxxx` 邀请链接不支持,改用数字 ID |
| 频道收不到新闻 | bot 是否已是频道管理员;`news_channel_id` 是否指向正确频道;Actions 是否变红(变红说明接口失败) |
| 频道 ID 怎么查 | server 模式启动后在频道发一条消息,看日志 `Channel post - channel_id: ...` |
| 推送时间不对 | 确认没有改动 `DAILY_PUSH_TIME` 的 `tzinfo=timezone.utc` 与两个 workflow 的 cron |
| Actions 成功但没收到消息 | 检查 `ADMIN_USER_ID` 是否是数字 ID,以及管理员是否先给 bot 发过消息 |
