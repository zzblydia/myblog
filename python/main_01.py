# Python 3.8.10

import asyncio
import websockets

async def handler(websocket, path):
    # 根据 path 选择不同的处理函数
    print(f"receive {websocket} request from path {path}")

    try:
        async for message in websocket:
            print(f"Received message: {message}")
            await websocket.send(f"Echo: {message}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print(f"Connection closed for ")

async def start_server():
    async with websockets.serve(handler, "", 8765):
        print("WebSocket server started at ws://0.0.0.0:8765")
        await asyncio.Future()  # 运行直到外部中断

# 使用 asyncio.run 启动事件循环
if __name__ == "__main__":
    asyncio.run(start_server())

"""
# python 3.12.3报错

WebSocket server started at ws://localhost:8765
connection handler failed
Traceback (most recent call last):
  File "D:\code\Storages\pythonProjects\tts_asr_server_demo_01\.venv\Lib\site-packages\websockets\asyncio\server.py", line 373, in conn_handler
    await self.handler(connection)
          ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: handler() missing 1 required positional argument: 'path'
"""