# MyTelegramBot

一个自用的 Telegram 机器人:查询 Singtel/t-sim 手机套餐余量,并推送给管理员。

支持两种运行方式,共用同一套查询逻辑:

- **server 模式**:进程常驻,实时响应管理员的查询指令,并在每天固定时间自动推送一次;
- **client 模式**:由外部定时器(GitHub Actions)触发,查询一次、推送一次、随即退出。

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

然后填写四个字段:

| 字段 | 含义 | 说明 |
|---|---|---|
| `bot_token` | BotFather 发放的 token | 必填;仍是 `REPLACE_WITH_...` 时程序会拒绝启动 |
| `admin_user_id` | 管理员的 Telegram 用户 ID | 为空时只记录消息、不响应任何指令、不推送 |
| `order_id` | 订单号,查询接口的 `reference` 参数 | 必填,否则查询会失败 |
| `run_mode` | `server` 或 `client` | 决定进程行为 |

示例(占位值,不能直接运行):

```json
{
    "bot_token"     : "REPLACE_WITH_BOT_TOKEN",
    "admin_user_id" : "123456789",
    "order_id"      : "123456",
    "run_mode"      : "server"
}
```

> `config.example.json` 只用于复制,程序**不会**回退读取它。这样占位 token 不会被误当成有效配置跑起来。

### 4. 运行

```bash
# 长期在线(server 模式)
.venv/bin/python main.py

# 一次性查询(client 模式):先把 run_mode 改成 client,再执行同一条命令
```

也可以直接在 PyCharm 里以 `main.py` 为脚本运行;注意 Working directory 必须是项目根目录 `python/MyTelegramBot`,否则 `bot/`、`init/`、`business/` 无法导入。

### 5. 机器人指令

| 指令 | 发送者 | 行为 |
|---|---|---|
| `/query singtel` | 仅 `admin_user_id` 本人 | 立即查询并回复套餐名称、失效时间、用量 |

其他人的消息、其他指令一律忽略;server 模式仍会记录消息日志。

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
│   ├── server.py               # Application、handler、私聊/群聊分派、命令响应
│   ├── client.py               # client 模式的一次性查询与发送
│   └── schedule.py             # 定时器注册 + 每日任务
├── init/                       # 基础设施层
│   ├── config.py               # load_config()
│   └── logger.py               # init_logging()
├── business/                   # 业务层
│   └── singtel.py              # 查询接口调用、签名、结果格式化
└── logs/                       # 运行时生成(忽略)
```

依赖方向严格单向,不存在循环导入:

```text
main.py ──> init.config / init.logger
   ├──> bot.client ──> business.singtel
   └──> bot.server ──> bot.schedule ──> business.singtel
                  └──> business.singtel
```

约束:`business/` 不 import telegram、不知道 `chat_id`、不发消息。

---

## 三、脚本功能

### main.py

1. `init_logging()`:先初始化日志(必须在读配置之前,配置告警才能落盘);
2. `load_config()`:读 `config/config.json`,缺失时抛出带修复提示的错误;
3. 校验 `bot_token` 非空且不是占位值;
4. 按 `run_mode` 分派:`client` → `asyncio.run(run_client(config))`,`server` → `run_server(config)`。

### server 模式(`bot/server.py` + `bot/schedule.py`)

- 构建 `Application`,配置写入 `bot_data["config"]`;
- 只注册**一个** `MessageHandler(filters.ALL, handle_message)`,内部按会话类型分派:
  - `handle_private_message()`:记录 user_id / 昵称 / 内容;
  - `handle_group_message()`:额外记录 group_id / 群名;
  - 两者都调用共用的 `_respond_admin_query()`,因此不会出现"同一消息被处理两次";
- `register_daily_job()` 注册每日任务;`job_queue` 为 `None`(缺 APScheduler)时直接报错退出,给出安装命令;
- `app.run_polling()` 阻塞运行。

### client 模式(`bot/client.py`)

- 不需要 `Application`,直接用 `async with Bot(...)` 发送一条消息;
- 未配置 `admin_user_id` 时记录错误并退出(退出码仍为 0,便于 Actions 保持绿色;若希望失败变红,可改为 `sys.exit(1)`)。

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

### 异常处理

`query_singtel_data()` 对外**永不抛异常**:

- 网络错误、HTTP 非 2xx、`code != 1`、`result` 为空、无可解析字段,统一记录 `logger.exception` 后返回 `查询失败: <原因>`;
- 因此 server / schedule / client 三个发送点各自只有一行发送代码,不需要重复 `try/except`。

### 定时与时区

- 推送时间:每天 **06:00 SGT(UTC+8)= 22:00 UTC**;
- 修改位置:`bot/schedule.py` 的 `DAILY_PUSH_TIME`;
- `tzinfo=timezone.utc` 必须保留,否则会按运行机器的本地时区解释。

### 已知限制

`requests.get()` 是同步调用,在 async handler 中执行最长会阻塞事件循环 30 秒,期间 bot 不处理其他消息。当前未做线程池改造。

---

## 五、GitHub Actions

工作流:`.github/workflows/daily_query.yml`

- 触发:每天 22:00 UTC(cron `0 22 * * *`)或手动 `workflow_dispatch`;
- 步骤:安装 `requirements.txt` → 用 Secrets 生成 `config/config.json` → `python main.py`;
- 需要的 Secrets:`BOT_TOKEN`、`ADMIN_USER_ID`、`ORDER_ID`;
- 由于 `config/` 里除模板外没有入库文件,workflow 直接写 `config/config.json` 即可,不需要 `mkdir`。

---

## 六、常见问题

| 现象 | 原因与处理 |
|---|---|
| `AttributeError: 'NoneType' object has no attribute 'run_daily'` | 缺 `[job-queue]`,执行 `pip install "python-telegram-bot[job-queue]"` |
| `配置文件不存在: .../config/config.json` | 未创建配置,按报错提示 `cp config/config.example.json config/config.json` |
| `bot_token 未配置或仍为占位值` | `config.json` 还是模板内容,填入真实 token |
| `ModuleNotFoundError: No module named 'bot'` | 用 `python main.py` 从项目根目录启动,或把 PyCharm 的 Working directory 设为项目根 |
| 推送时间不对 | 确认没有改动 `DAILY_PUSH_TIME` 的 `tzinfo=timezone.utc` |
| Actions 成功但没收到消息 | 检查 `ADMIN_USER_ID` 是否是数字 ID,以及管理员是否先给 bot 发过消息 |
