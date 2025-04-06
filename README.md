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


## 命名原则

根据 Python 的最佳实践和代码可读性，建议采用以下命名规范：

1. **模块文件（.py文件）**：
   - 使用小写字母加下划线（snake_case）
   - 例如：`feishu.py`, `webhook.py`, `const.py`
   - 原因：这是 Python 社区的标准做法，符合 PEP 8 规范

2. **类文件**：
   - 使用驼峰命名法（CamelCase）
   - 例如：`BaseModel.py`, `FeishuBase.py`
   - 原因：类名通常使用驼峰法，这样更容易识别类的定义

3. **目录名**：
   - 使用小写字母加下划线
   - 例如：`feishu/`, `utils/`
   - 原因：保持与模块命名一致

4. **特殊文件**：
   - `__init__.py` 保持原样（这是 Python 包的标准命名）
   - `__pycache__` 保持原样（这是 Python 的标准目录）

这样的命名规范有以下优点：
1. 符合 Python 社区规范
2. 提高代码可读性
3. 便于区分模块和类
4. 保持一致性
5. 避免命名冲突





## 封装更新

修改setup.py中的版本
```python
    version="xxx",
```
运行构建脚本
```bash
python build_package.py
```
发布
```bash
twine upload dist/*
```

## 许可证

MIT
