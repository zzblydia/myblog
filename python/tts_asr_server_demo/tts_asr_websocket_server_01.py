# 未完成

import asyncio
import websockets


async def handler_path1(websocket, path):
    async for message in websocket:
        response = f"Received on path1: {message}"
        await websocket.send(response)


async def handler_path2(websocket, path):
    async for message in websocket:
        response = f"Received on path2: {message}"
        await websocket.send(response)


async def handler_path3(websocket, path):
    async for message in websocket:
        response = f"Received on path3: {message}"
        await websocket.send(response)


async def main(websocket, path):
    # 根据 path 选择不同的处理函数
    if path == "/path1":
        await handler_path1(websocket, path)
    elif path == "/path2":
        await handler_path2(websocket, path)
    elif path == "/path3":
        await handler_path3(websocket, path)
    else:
        # 对于不匹配的 path，返回 400 Bad Request
        await websocket.close(code=websockets.CLOSE_CODE_PROTOCOL_ERROR)


start_server = websockets.serve(main, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
print("WebSocket server started at ws://localhost:8765")
asyncio.get_event_loop().run_forever()
