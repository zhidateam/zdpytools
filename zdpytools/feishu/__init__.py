"""
飞书API集成模块 - 提供飞书开放平台API的封装
"""
from .Feishu import Feishu
from .webhook import send_wehbook
#防止模块内部的其他变量、函数或类被意外导入
__all__ = ["Feishu", "send_wehbook"]