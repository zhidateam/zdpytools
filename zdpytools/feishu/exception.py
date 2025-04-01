
class LarkException(Exception):
    def __init__(self, code=0, msg=None, url=None, req_body=None, headers=None):
        self.url = url
        self.req_body = req_body
        self.code = code
        self.msg = msg
        self.headers = headers

    def __str__(self) -> str:
        return f"code:{self.code} | msg:{self.msg} | url:{self.url} | headers:{self.headers} | req_body:{self.req_body}"

    __repr__ = __str__