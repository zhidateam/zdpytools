"""
AIHubMax API异常类定义
"""

class AIHubMaxException(Exception):
    """
    AIHubMax API异常基类
    """
    def __init__(self, code=None, msg=None, url=None, req_body=None, headers=None):
        self.code = code
        self.msg = msg
        self.url = url
        self.req_body = req_body
        self.headers = headers
        
        error_message = f"AIHubMax API错误 - 代码: {code}, 消息: {msg}"
        if url:
            error_message += f", URL: {url}"
        
        super().__init__(error_message)
    
    def __str__(self) -> str:
        return f"code:{self.code} | msg:{self.msg} | url:{self.url} | headers:{self.headers} | req_body:{self.req_body}"
    
    __repr__ = __str__
