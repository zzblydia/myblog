# 未完成

import asyncio
import websockets
import json
import uuid

# 用于存储每个连接的 trace_id 和接收到的数据包计数器
connections = {}

async def handler(websocket, path):
    connection_id = str(uuid.uuid4())
    connections[connection_id] = {
        "trace_id": None,
        "packet_count": 0,
    }
    
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                # 处理二进制数据包，增加计数器
                connections[connection_id]["packet_count"] += 1
                
                # 获取当前的数据包计数器值和 trace ID 
                packet_count = connections[connection_id]["packet_count"]
                
                if packet_count == 10 or :
                    trace_id = connections[connection_id]["trace_id"]
                    response_event = {
                        "resp_type": "EVENT",
                        "trace_id": trace_ID,
                        "event": "VOICE_START",
                        "timestamp": 1500,  
                    }
                    await websocket.send(json.dumps(response_event))
                elif packet_count == 250:
                    trace_id = connections[connection_id]["trace_id"]
                    response_event = {
                        "resp_type": "EVENT",
                        "trace_id": trace_ID,
                        "event": "VOICE_END",
                        "timestamp": 1500,  
                    }
                    await websocket.send(json.dumps(response_event))
                elif packet_count == 200:
                    trace_ID=connections[connection_ID]['trace_ID']
                    
                    response_result={
                      'resp_type': 'RESULT',
                      'trace id': trace_ID ,
                      'segments': [
                          {
                              'start_time':100,
                              'end_time':1500,
                              'is_final': False,
                              'result':
                                  {
                                      'text':'第一句中间结果',
                                      ‘word_info’:[
                                          {'start_time’:100,'end_time’:800,'word':'第一'},
                                          {'start_time’:800,'end_time’:1000,'word':'句'},
                                          {'start time’ :1000,’end time’ :1500,’word’:'结果'}
                                      ],
                                      ‘score’:0.00 
                                  },
                          },
                      ]
                  }

                  await websocket.send(json.dumps(response_result))
                    
            else: 
                data=json.loads(message)
                
                 if path== '/v1/abc/rasr/sentence-stream':
                     if data.get("command")=="START":
                         TraceID=str(uuid.uuid4())
                         Connections [Connection id]['Trace ID']=TraceID

                         response={
                             ‘resp_type‘:‘START‘，
                             ’trace id‘: TraceID  
                         }

                     await websocket.send(json.dumps(response))

                 elif path== '/v1/abc/rasr/continue-stream':
                     current_trace=connections [Connection ID]['Trace ID']
                     
                     response={
                          ’resp type'：'CONTINUE'，
                           ’TraceID'：current_trace  
                       }

                   await websocket.send(json.dumps(response))

                 # 检查是否为结束命令并处理清理资源和断开连接逻辑                 
                 elif data.get("command") == "END" and not data.get("cancel"):
                     trace_ID=connections[connection_Id]['Trace ID']
                     
                     end_response={
                         “resp_type”: “END”,
                         “trace id”: TraceID ,
                         “reason”: “NORMAL” 
                       }
                       
                   await websockets.send（json.dumps(end_response））
                   break   # 跳出循环以关闭连接
    
   except json.JSONDecodeError：
       await websockets.send（json.dumps({"error":"Invalid JSON"}））
    
   finally：
       # 清理资源并关闭该连接   
       del Connections [Connection Id]
       print(f"Connection {connect.id} closed.")

# 启动 WebSocket 服务端   
start_server=websockets.serve(handler，'localhost',8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
