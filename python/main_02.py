# Python 3.8.10

import asyncio
import websockets
import json
import uuid

# 用于存储每个连接的 trace_id 和接收到的数据包计数器
connections = {}

async def handler(websocket, path):
    print(f'receive request from path {path}')

# 启动 WebSocket 服务端   
start_server=websockets.serve(handler, '',8766)
print("WebSocket server started at ws://0.0.0.0:8766")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

"""
# python 3.12.3报错

Traceback (most recent call last):
  File "/opt/auth_server/venv/bin/../../main_02.py", line 15, in <module>
    start_server=websockets.serve(handler, 'localhost',8000)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/auth_server/venv/lib/python3.12/site-packages/websockets/asyncio/server.py", line 737, in __init__
    self.server = Server(
                  ^^^^^^^
  File "/opt/auth_server/venv/lib/python3.12/site-packages/websockets/asyncio/server.py", line 281, in __init__
    self.loop = asyncio.get_running_loop()
                ^^^^^^^^^^^^^^^^^^^^^^^^^^
RuntimeError: no running event loop
"""