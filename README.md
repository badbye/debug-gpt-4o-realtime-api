1. 打日志。修改 livekit 包的文件，`site-packages/livekit/plugins/openai/realtime/realtime_model.py`

   
```python
ai_logger = None
def get_ai_logger():
    global ai_logger
    if ai_logger:
        return ai_logger
    import time
    now_time = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())
    logger = logging.getLogger(f"ai_logger_{now_time}")
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(f"ai_logger_{now_time}.log")
    formatter = logging.Formatter('{"timestamp": "%(asctime)s", "data": %(message)s}')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    ai_logger = logger
    return ai_logger
```


```
class RealtimeSession(utils.EventEmitter[EventTypes]):
    def __init__(self, ...) -> None:
        # ... 
        self._ai_logger = get_ai_logger()
    
    @utils.log_exceptions(logger=logger)
        async def _send_task():
            nonlocal closing
            async for msg in self._send_ch:
                self._ai_logger.info(json.dumps(msg)) # 添加日志
                await ws_conn.send_json(msg)

            closing = True
            await ws_conn.close()
    
    @utils.log_exceptions(logger=logger)
    async def _recv_task():
        while True:
            # ...
            try:
                data = msg.json()
                self._ai_logger.info(json.dumps(data))  # 添加日志
                # ...
```


2. 可视化日志

```bash
python3 main.py
```

页面中，输入日志路径。