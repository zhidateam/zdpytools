# zdpytools

Python工具集，提供日志和飞书API集成功能。

## 功能

- **日志工具**：基于loguru的简单易用的日志模块
- **飞书API**：飞书开放平台API的封装，支持多维表格操作

## 安装

```
pip install zdpytools
```

## 使用示例

### 日志工具

```python
from zdpytools.utils.log import logger

logger.info("这是一条信息日志")
logger.error("这是一条错误日志")
```

### 飞书API

```python
import asyncio
from zdpytools.feishu import Feishu

async def example():
    fs = Feishu(app_id="你的飞书应用ID", app_secret="你的飞书应用密钥")
    try:
        # 查询多维表格记录
        result = await fs.bitable_records_search("app_token", "table_id")
        print(result)
    finally:
        await fs.close()

asyncio.run(example())
```

## 许可证

MIT
