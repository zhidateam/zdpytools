"""
AutoDL API异常类定义
"""

class AutoDLException(Exception):
    """
    AutoDL API异常基类
    """
    def __init__(self, code=None, msg=None, url=None, req_body=None, headers=None):
        self.code = code
        self.msg = msg
        self.url = url
        self.req_body = req_body
        self.headers = headers
        
        error_message = f"AutoDL API错误 - 代码: {code}, 消息: {msg}"
        if url:
            error_message += f", URL: {url}"
        
        super().__init__(error_message)
