# MyTelegramBot
MyTelegramBot is a python project for my telegram bot to help my life.

## 总体约束
1. 项目基于开源代码`python-telegram-bot`
2. 脚本运行环境 python 3.10.2
3. 脚本启动后先初始化日志模块,日志文件命名默认是时间戳, 默认级别是info,只输出到文件, 不输出到控制台.
4. 脚本可以通过github action定时运行.
5. 请保持脚本的功能相对独立 如果有可能 日志部分/配置部分使用单独的文件

## 主要文件
- `my_telegram_bot.py` 主脚本,功能包括日志初始化,配置读取,bot启动,监听消息
- `query_mobile_data.py` 功能脚本, 发送查询请求和处理响应,并返回关注信息
- `bot_logger.py` 日志模块,初始化文件日志
- `bot_config.py` 配置模块,读取`config.json`
- `config.json` 配置文件,包含bot_token/admin_user_id/order_id/run_mode
- `.github/workflows/daily_query.yml` GitHub Actions定时任务

## 运行环境
- 虚拟环境目录: `venv/`
- 依赖安装: `venv/bin/pip install "python-telegram-bot[job-queue]" requests`
- 启动命令: `venv/bin/python3 my_telegram_bot.py`

### 主要功能
- 查询手机套餐余量,并发送给管理员.  
- 接收管理员的查询请求,查询手机套餐余量并响应.  

查询功能分两种情况,需要同时支持:  
1.脚本长期运行,bot长期在线,bot定时查询(每天一次)并发送给管理员.  
2.脚本定时运行,bot查询并发送给管理员.  
运行模式通过`config.json`中的"run_mode"决定, `server`代表长期运行,`client`代表定时运行.  

### 详细逻辑
1.脚本启动后, 读取当前目录的配置文件`config.json`.其内容格式示例如下:
```
{
    "bot_token" : "abc",
    "admin_user_id" : "12345",
    "order_id" : "123456",
    "run_mode" : "server" 
}
```
如果管理员还没关注机器人, 则`admin_user_id`可能为空.此时只按照后续要求打印消息,不做任何响应.  

2.脚本启动后, 监听收到的个人消息和所在的群组消息.  
如果是个人消息, 打印用户id,用户昵称,用户消息.  
如果是群主消息, 打印群组id,用户id,群组名称,用户昵称,用户消息  

3.如果消息发送用户的id是管理员, 且消息内容符合以下, 则响应. 其他人的消息则忽略.
- /query singtel

4.打开如下页面, 输入`order_id`,并进行查询:
```
https://search.t-sim.hk/dataplan/order
```
脚本通过发送http请求查询.发送请求时请模拟windows下的chrome浏览器, 发送的请求内容和响应内容可以通过debug日志打印.  
http请求的内容请参照`http_request.txt`, http响应的内容格式请参照`http_response.json`.  
警告:这两个文件的内容可能很有隐私敏感数据,内容和格式仅供参考, 请在本地使用工具处理,禁止使用互联网传输.  

实际API端点: `https://api.tsimtech.com/tsim/shopify/getGygPlanInfo?reference={order_id}`  
认证方式: 每次请求动态生成签名头,算法已在`query_mobile_data.py`中实现,无需手动维护.  

5.对于响应的json,关注信息是
 - channel_dataplan_name 套餐名称(字符串)  
 - expire_time 失效时间(格式 2026-01-01 11:11:11)  
 - data_usage 用量,单位M(格式 1234.56)  
 对于异常,仅返回正常字段即可.  

6.bot返回关注信息给管理员.

## GitHub Actions
- 工作流文件: `.github/workflows/daily_query.yml`
- 触发方式: 定时(cron)
- 运行模式: `client`(一次性查询后退出)
- 敏感配置通过GitHub Secrets注入,在workflow中生成`config.json`
- 所需Secrets: `BOT_TOKEN`, `ADMIN_USER_ID`, `ORDER_ID`
