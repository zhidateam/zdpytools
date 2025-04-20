"""
AIHubMax API集成模块 - 提供AIHubMax API的异步封装
"""
from .client import AIHubMaxClient
from .exception import AIHubMaxException
from .const import *

# 防止模块内部的其他变量、函数或类被意外导入
__all__ = ["AIHubMaxClient", "AIHubMaxException"]
