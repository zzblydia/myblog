# WebSocket 音频流提取工具

从**单个 pcap** 中提取 WebSocket 音频流，最终合并为一个音频文件。工具分为两个阶段：

1. `ws_payload_dump.py`：调用 tshark 完成 TLS 解密、TCP 重组和 HTTP/WebSocket 识别，解析 WebSocket 帧，生成中间文件 `.payload`。
2. `ws_payload_decode.py`：读取 `.payload`，按顺序解码音频分片，合并为一个音频文件。

```
pcap ──tshark──> 重组后的 TCP/TLS 字节流 ──Python──> .payload ──解码──> audio.pcm / audio.wav
```

## 环境要求

- Python 3.13（仅使用标准库）
- TShark / Wireshark 4.x（验证版本：`TShark (Wireshark) 4.4.18`）
- 测试脚本额外需要 `tcpdump`、`openssl`

## 快速开始

### 二进制音频（服务端 -> 客户端）

```bash
python3 ws_payload_dump.py \
    --pcap capture.pcap \
    --out audio.payload \
    --type binary \
    --direction s2c

python3 ws_payload_decode.py \
    --input audio.payload \
    --type binary \
    --out audio.pcm
```

### JSON + Base64 音频

```bash
python3 ws_payload_dump.py \
    --pcap capture.pcap \
    --out audio.payload \
    --type text \
    --direction s2c

# 递归查找 JSON 中所有名为 audio 的键
python3 ws_payload_decode.py \
    --input audio.payload \
    --type text \
    --key audio \
    --out audio.pcm
```

### 带 WAV 头输出

```bash
python3 ws_payload_decode.py \
    --input audio.payload \
    --type binary \
    --out audio.wav \
    --wav --rate 16000 --channels 1 --bits 16
```

### TLS 加密会话

```bash
python3 ws_payload_dump.py \
    --pcap capture.pcap \
    --keylog keys.log \
    --out audio.payload \
    --type binary \
    --direction s2c
```

## 第一阶段：`ws_payload_dump.py`

### 工作原理

- `tshark -z follow,tls,raw`（明文用 `follow,tcp,raw`）给出**完整重组后的字节流**。
- Python 自己解析 WebSocket 帧，处理：
  - 客户端帧的掩码（mask）
  - 分片消息（continuation frame）
  - `permessage-deflate` 压缩，包括跨消息的上下文保留（context takeover）
  - 控制帧（ping/pong/close）跳过
- 这样做的原因：Wireshark 4.4 的 WebSocket 解析器存在一个已知缺陷——当 HTTP 101 响应和第一批 WebSocket 帧落在同一个 TCP 段或同一个 TLS record 中时，整段字节会被交给 HTTP 层，WebSocket 解析器不会再回看这批帧。使用 `follow` 字节流可以绕开该缺陷。
- 如果字节流无法识别为 WebSocket，会回退到 PDML 解析路径（`tshark -T pdml`），用于兼容特殊抓包。

### 主要参数

| 参数 | 说明 |
| --- | --- |
| `--pcap FILE` | 输入 pcap/pcapng |
| `--out FILE` | 输出 `.payload`，默认 `<pcap>.payload` |
| `--keylog FILE` | TLS keylog 文件 |
| `--stream N` | 指定 `tcp.stream`；默认自动选择唯一的 WebSocket 流 |
| `--server-port N` | 服务端端口，用于 `s2c`/`c2s` 判定 |
| `--direction auto\|s2c\|c2s\|both` | 提取哪个方向，默认 `auto` |
| `--type auto\|binary\|text` | `.payload` 的格式，默认 `auto` |
| `--invalid-text error\|skip\|b64` | 文本消息不是合法 JSON 时的行为 |
| `--on-decompress-error error\|skip` | deflate 解压失败时的行为 |
| `--decode RULE` | 额外的 tshark `-d` 规则，如 `tcp.port==8443,tls` |
| `--probe` | 打印诊断信息后继续提取 |
| `--selftest` | 运行内置测试 |
| `--log-file FILE` | 日志文件，默认 `ws_payload_dump_<时间戳>.log` |
| `--log-level LEVEL` | `DEBUG`/`INFO`/`WARNING`/`ERROR`，默认 `INFO` |
| `--no-log-file` | 只输出到控制台 |

### 方向选择

- `auto`：只有**一个方向**存在完整数据消息时自动选择；两个方向都有数据消息时报错，要求显式指定。
- `s2c`：服务端 -> 客户端，通常音频下行使用该方向。
- `c2s`：客户端 -> 服务端。
- `both`：两个方向按到达顺序合并（跨方向的精确时序只能近似，通常不建议使用）。

服务端/客户端端口优先从 TCP SYN 推断；如果 SYN 缺失，则从 HTTP Upgrade 的请求/响应方向推断。

### 类型选择

- `auto`：由**第一条完整数据消息**决定；后续出现另一种类型会报错，避免静默丢数据。
- `binary`：只提取二进制消息。
- `text`：只提取文本消息。

### `.payload` 格式

#### 二进制

整个文件是所有二进制消息载荷的**原始拼接**，没有分隔符、没有索引文件：

```
message1 || message2 || message3 ...
```

#### 文本

UTF-8 JSON Lines，每行一个完整 JSON 文档：

```
{"type":"audio","seq":1,"data":{"audio":"..."}}
{"type":"audio","seq":2,"data":{"audio":"..."}}
```

- 原始 JSON 可能是多行（pretty print），提取时会压缩成一行。
- 压缩只删除字符串外的空白，不重新序列化：键顺序、重复键、数字格式、Base64 内容都会保留。
- 文本消息必须是合法 JSON；否则按 `--invalid-text` 处理：
  - `error`（默认）：报错
  - `skip`：跳过
  - `b64`：写成 `{"__raw_b64__":"..."}` 以保留原始文本

### TLS 注意事项

1. **必须抓到 TLS 握手**。只有 keylog 而没有握手包，TLS 1.3 无法推导会话密钥，tshark 也不能解密。
2. libwebsockets 写 keylog 时会在环境变量值后追加 vhost，因此实际文件名通常是 `$SSLKEYLOGFILE.<vhost>`，而不是裸路径。把包含密钥的那个文件传给 `--keylog`。
3. keylog 中的 `#` 注释行 Wireshark 会忽略；客户端和服务端重复写入同一文件也没有问题。
4. 服务端使用了 ALPN `http/1.1` 时，Wireshark 更容易在解密后识别 HTTP。
5. 非标准 TLS 端口如果无法自动识别，可加：
   ```bash
   --decode tcp.port==8443,tls
   ```
6. 如果 keylog 不属于该会话，会看到 `http 101 responses=0` 的诊断。

### 诊断

`--probe` 会打印：

- tshark 版本
- 找到的 WebSocket `tcp.stream`
- 客户端/服务端端口
- PDML 解析出的消息数
- 字节流解析出的消息数
- TLS handshake 帧数、HTTP 101 响应数

如果两个消息数不一致，通常就是“101 响应与首批帧合并”导致的，本工具会使用字节流解析结果。

也可以手动查看重组后的字节流：

```bash
# 明文
tshark -r capture.pcap -q -z follow,tcp,raw,0

# TLS
tshark -r capture.pcap -o tls.keylog_file:keys.log -q -z follow,tls,raw,0
```

输出中 `Node 0`/`Node 1` 是两端地址，行首有制表符的是 `Node 1`，每行是该方向的一段十六进制字节。把它按方向拼接后，应该能在 HTTP Upgrade 之后看到 `81/82/88` 等 WebSocket 帧头。

常见错误：

| 现象 | 处理 |
| --- | --- |
| `no WebSocket stream found` | 确认抓包包含 HTTP Upgrade；TLS 确认 `--keylog` 正确 |
| `protected by TLS; pass --keylog` | 加上 `--keylog` |
| `both directions carry complete WebSocket data messages` | 显式指定 `--direction s2c` 或 `c2s` |
| `mixed payload types` | 显式指定 `--type binary` 或 `text` |
| `capture contains multiple WebSocket streams` | 用 `--stream N` 指定 |
| `continuation frame without an open message` | 抓包从分片消息中间开始，无法重组；从会话开始处重新抓包 |

## 第二阶段：`ws_payload_decode.py`

### 主要参数

| 参数 | 说明 |
| --- | --- |
| `--input FILE` | 输入 `.payload` |
| `--out FILE` | 输出音频文件 |
| `--type binary\|text` | 输入格式 |
| `--key KEY` | 文本模式下音频所在的 JSON 键 |
| `--value-encoding base64\|raw` | JSON 值如何表示音频字节，默认 `base64` |
| `--invalid-json error\|skip` | 文本模式下的 JSON 解析失败行为 |
| `--wav` | 给原始 PCM 加 WAV 头 |
| `--rate N` | WAV 采样率，默认 16000 |
| `--channels N` | WAV 声道数，默认 1 |
| `--bits N` | WAV 位深，默认 16 |
| `--list-keys` | 列出文本 payload 中出现过的 JSON 键路径后退出 |
| `--selftest` | 运行内置测试 |

### JSON 键查找

- 简单名字（如 `--key audio`）：**递归**查找任意层级中所有同名键。
- 精确路径（如 `--key data.audio`）：只匹配该路径。
- 支持数组下标：`--key result.items[0].audio`。
- 同一个 JSON 文档中命中多个键时，按文档顺序依次拼接。
- 值为字符串或字符串数组；字符串数组中的每一项按顺序拼接。

Base64 解码兼容：

- 标准 Base64 和 URL-safe Base64（`-`/`_`）
- 缺少 `=` 填充
- `data:audio/...;base64,...` 形式的 Data URI
- 字符串中的空白字符会被忽略

`--value-encoding raw` 表示 JSON 字符串本身就是音频字节（按 UTF-8 编码），不做 Base64 解码。

## 测试

### 内置自测

```bash
python3 ws_payload_dump.py --selftest --no-log-file
python3 ws_payload_decode.py --selftest --no-log-file
```

第一阶段自测会动态构造确定性 pcap，覆盖：

- 单帧二进制、分片消息、同一 TCP 段内多条消息、16 位扩展长度
- 文本 JSON、跨行 JSON、控制消息、同段多消息
- `permessage-deflate` 二进制/文本
- 方向过滤（s2c / c2s）

### 真实抓包端到端测试

```bash
tests/capture_e2e.sh
```

脚本会：

1. 启动真实的 Python WebSocket mock 服务端；
2. 在 `lo` 上用 `tcpdump` 抓包；
3. 运行真实的 mock 客户端；
4. 分别执行两个阶段；
5. 用 sha256 比较最终音频与对端实际发送的字节。

覆盖用例：

- 明文 s2c 二进制/文本
- 明文 c2s 二进制/文本（客户端掩码、分片）
- TLS s2c 二进制/文本（含 101 与首批帧合并的情况）
- TLS c2s 二进制（客户端掩码）
- 明文/TLS 下的 `permessage-deflate`

调试时可保留现场：

```bash
KEEP=1 tests/capture_e2e.sh
```

## 已知限制

- 一个 pcap 只处理一个 WebSocket 会话；多个会话需用 `--stream` 指定。
- TLS 抓包必须包含握手；明文抓包如果没有 HTTP Upgrade，需要 `--stream` 且抓包必须从帧边界开始。
- 文本消息必须是合法 JSON；否则使用 `--invalid-text b64` 保留原始内容。
- 当前字节流解析会把解析后的消息保存在内存中；超大抓包建议先按时间/大小切分。
- `both` 方向的合并顺序是到达顺序的近似值。
