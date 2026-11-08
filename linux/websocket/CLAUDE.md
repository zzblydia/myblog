# WebSocket 音频流提取工具：实现说明

## 目标

从一个 pcap 中提取单个 WebSocket 会话的音频数据，输出一个合并后的音频文件。工具分为两阶段：

1. `ws_payload_dump.py`：pcap -> `.payload`
2. `ws_payload_decode.py`：`.payload` -> 音频文件

详细用法见 `README.md`，本文只记录实现方案和关键决策。

## 数据流

```
pcap
  └─ tshark（TLS 解密、TCP 重组、HTTP/WebSocket 识别）
       └─ tshark -z follow,tls,raw / follow,tcp,raw
            └─ Python WebSocket 帧解析器
                 └─ .payload
                      └─ ws_payload_decode.py
                           └─ audio.pcm / audio.wav
```

## 关键实现

### 1. 为什么不用纯 PDML

Wireshark 4.4 的 WebSocket 解析器存在一个限制：如果 HTTP 101 响应和第一批 WebSocket 帧位于同一个 TCP 段或同一个 TLS record 中，整段字节会被交给 HTTP 层，WebSocket 解析器不会再回看。表现是 PDML 只输出后续帧，首批音频丢失。

因此主路径改为解析 `tshark -z follow,tls,raw`（明文用 `follow,tcp,raw`）输出的完整重组字节流。PDML 仅作为无法识别字节流时的回退路径。

### 2. 字节流解析器

`ws_payload_dump.py` 中的 `collect_stream_messages()` 及以下类：

- `_iter_follow_output()`：逐行读取 follow 输出，解析 `Node 0/1` 端点和十六进制数据块。
- `_DirectionState`：先缓存并解析 HTTP Upgrade 头，再把剩余字节交给帧解析器。如果抓包从会话中间开始（首字节不是 `G`/`H`），直接把缓冲区当作帧数据。
- `_FrameAssembler`：增量解析 WebSocket 帧：
  - 2/4/10 字节帧头、16/64 位扩展长度
  - 客户端掩码
  - 分片消息（opcode 0 continuation）
  - 控制帧（ping/pong/close）跳过，且允许穿插在分片消息中
  - `permessage-deflate`：每个方向一个 `zlib.decompressobj(-15)`，跨消息保留上下文（context takeover），解压前补回 `00 00 ff ff`
- `_StreamSession`：按到达顺序保存完整消息，并记录每个源端口的数据消息数。

### 3. 方向与类型判定

- 端口优先从 TCP SYN 推断；SYN 缺失时从 HTTP 请求/101 响应的方向推断。
- `--direction auto`：只有一个方向有数据消息时自动选择；两个方向都有则报错。
- `--direction both`：按到达顺序合并两个方向。
- `--type auto`：第一条完整数据消息决定类型；后续出现另一种类型立即报错，避免静默丢数据。

### 4. `.payload` 格式

- 二进制：所有消息载荷原始拼接，无分隔符、无索引。
- 文本：UTF-8 JSON Lines，每行一个完整 JSON。
  - 多行 JSON 会压缩成一行。
  - 压缩是词法处理，不重新序列化，保留键顺序、重复键、数字格式和 Base64 内容。

### 5. 第二阶段解码

- 二进制：校验后复制，可选加 WAV 头。
- 文本：
  - `--key audio`：递归查找任意层级的同名键。
  - `--key data.audio`：精确路径；支持 `items[0].audio`。
  - 同一文档多个命中按文档顺序拼接。
  - Base64 兼容标准/URL-safe、缺失填充、Data URI。
  - `--value-encoding raw` 支持 JSON 字符串直接作为字节。
- 输出使用临时文件 + rename，失败不会留下半个文件。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `ws_payload_dump.py` | 第一阶段：pcap -> `.payload` |
| `ws_payload_decode.py` | 第二阶段：`.payload` -> 音频 |
| `tests/ws_pcap_builder.py` | 动态构造确定性 pcap，用于第一阶段自测 |
| `tests/ws_mock_common.py` | mock 客户端/服务端共享的 WebSocket/TLS 辅助函数 |
| `tests/mock_ws_server.py` | 真实 WebSocket mock 服务端 |
| `tests/mock_ws_client.py` | 真实 WebSocket mock 客户端 |
| `tests/capture_e2e.sh` | tcpdump 真实抓包端到端测试 |
| `README.md` | 使用文档 |

## 测试

```bash
python3 ws_payload_dump.py --selftest --no-log-file
python3 ws_payload_decode.py --selftest --no-log-file
tests/capture_e2e.sh
```

端到端测试使用真实 Python 客户端/服务端 + `tcpdump -i lo`，覆盖：

- 明文 s2c/c2s、二进制/文本、客户端掩码与分片
- TLS s2c/c2s（含 101 与首批帧合并）
- 明文/TLS 下的 `permessage-deflate`
- 用 sha256 比较最终音频与对端实际发送的字节

## 验证环境

- Python 3.13
- TShark (Wireshark) 4.4.18
- Linux loopback 抓包

## 注意事项

- 一个 pcap 只处理一个 WebSocket 会话；多个会话用 `--stream N`。
- TLS 抓包必须包含握手，否则 keylog 也无法解密。
- libwebsockets 的 keylog 实际文件名通常是 `$SSLKEYLOGFILE.<vhost>`。
- 明文抓包若缺少 HTTP Upgrade，需要 `--stream N`，且抓包必须从帧边界开始。
- 当前实现会把解析后的消息保存在内存中；超大抓包建议先切分。
