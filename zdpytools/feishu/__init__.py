"""
飞书API集成模块 - 提供飞书开放平台API的封装
"""

import sys
import os
import json
from urllib.parse import urlencode, unquote
import httpx
import time
import asyncio

# 获取当前包的日志工具
from ..utils.log import logger

# 常量定义
lark_host = "https://open.feishu.cn"
TENANT_ACCESS_TOKEN_URI = "/open-apis/auth/v3/tenant_access_token/internal"
BITABLE_RECORDS = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records"
# 查询记录文档：https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-record/search
BITABLE_RECORDS_SEARCH = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/search"
BITABLE_RECORD = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/:record_id"
# 批量获取记录 https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-record/batch_get
BATCH_RECORDS = "https://open.feishu.cn/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/batch_get"

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

class Feishu:
    def __init__(self, app_id=os.getenv("FEISHU_APP_ID"), app_secret=os.getenv("FEISHU_APP_SECRET"), print_feishu_log=True):
        if not app_id or not app_secret:
            raise ValueError("app_id 或 app_secret 为空")
        self._app_id = app_id
        self._app_secret = app_secret
        self.print_feishu_log = print_feishu_log
        self._tenant_access_token = ""
        self._token_expire_time = 0  # 记录token过期时间
        self.client = httpx.AsyncClient(timeout=10.0)

    def _is_token_expired(self):
        """
        检查当前 token 是否过期
        """
        # 提前5分钟刷新 token，避免正好在过期边缘
        return time.time() >= (self._token_expire_time - 300)

    async def _authorize_tenant_access_token(self):
        """
        使用 httpx 异步请求获取 tenant_access_token
        """
        url = f"{lark_host}{TENANT_ACCESS_TOKEN_URI}"
        req_body = {"app_id": self._app_id, "app_secret": self._app_secret}
        headers = {"Content-Type": "application/json"}
        try:
            response = await self.client.post(url, json=req_body, headers=headers)
            response.raise_for_status()
            resp_data = response.json()
            self._tenant_access_token = resp_data.get("tenant_access_token", "")
            expire = resp_data.get("expire", 3600)  # 默认1小时过期
            self._token_expire_time = time.time() + expire  # 记录过期时间
            if self.print_feishu_log:
                logger.info(f"获取 tenant_access_token 成功: {self._tenant_access_token}")
        except httpx.HTTPError as e:
            logger.error(f"获取 tenant_access_token 失败: {e}")
            raise LarkException(code=-1, msg=f"请求失败: {e}", url=url, req_body=req_body, headers=headers)
        except json.JSONDecodeError as e:
            logger.error(f"解析 token 响应失败: {e}")
            raise LarkException(code=-1, msg="响应解析失败", url=url, req_body=req_body, headers=headers)

    async def _authorize_tenant_access_token_if_needed(self):
        """
        如果没有 token 或 token 已过期，则获取新 token
        """
        if not self._tenant_access_token or self._is_token_expired():
            await self._authorize_tenant_access_token()

    async def req_feishu_api(self, method, url, req_body=None, check_code=True, check_status=True):
        """
        发起飞书 API 异步请求
        """
        await self._authorize_tenant_access_token_if_needed()

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self._tenant_access_token,
        }

        if self.print_feishu_log:
            logger.debug(f"{method} 请求飞书接口: {unquote(url)}")
            logger.debug(f"请求体: {req_body}")

        try:
            if method.upper() == "GET":
                response = await self.client.get(url, headers=headers)
            elif method.upper() in ["POST", "PUT", "DELETE"]:
                response = await self.client.request(method.upper(), url, headers=headers, json=req_body)
            else:
                raise ValueError(f"不支持的请求方法: {method}")

            if check_status and response.status_code != 200:
                logger.error(f"HTTP 状态码异常: {response.status_code}, 响应内容: {response.text}")
                raise LarkException(code=response.status_code, msg="HTTP状态码异常", url=url, req_body=req_body, headers=headers)

            resp_data = response.json()

            if self.print_feishu_log:
                logger.debug(f"飞书接口响应: {resp_data}")

            if check_code and resp_data.get("code", -1) != 0:
                logger.error(f"接口返回错误, URL: {url}, 错误信息: {resp_data}")
                raise LarkException(code=resp_data.get("code"), msg=resp_data.get("msg"), url=url, req_body=req_body, headers=headers)

            return resp_data
        except httpx.HTTPError as e:
            logger.error(f"请求飞书接口异常: {e}, URL: {url}")
            raise LarkException(code=-1, msg=f"请求失败: {str(e)}", url=url, req_body=req_body, headers=headers)
        except json.JSONDecodeError as e:
            logger.error(f"解析响应 JSON 失败: {e}, URL: {url}")
            raise LarkException(code=-1, msg="响应解析失败", url=url, req_body=req_body, headers=headers)

    async def bitable_records_search(self, app_token, table_id, param={}, req_body={}, **kwargs):
        """
        根据条件查询多维表格记录
        """
        await self._authorize_tenant_access_token_if_needed()
        url = f"{lark_host}{BITABLE_RECORDS_SEARCH}"
        url = url.replace(":app_token", app_token).replace(":table_id", table_id)
        if param:
            url = url + "?" + urlencode(param)
        resp = await self.req_feishu_api("POST", url=url, req_body=req_body)
        return resp.get("data")

    async def bitable_record(self, app_token, table_id, record_id, **kwargs):
        """
        根据 record_id 查询单条记录
        """
        await self._authorize_tenant_access_token_if_needed()
        url = f"{lark_host}{BITABLE_RECORD}"
        url = url.replace(":app_token", app_token).replace(":table_id", table_id).replace(":record_id", record_id)
        resp = await self.req_feishu_api("GET", url=url)
        return resp.get("data")

    async def batch_get_records(self, app_token, table_id, record_ids, **kwargs):
        """
        批量获取多维表格记录
        """
        await self._authorize_tenant_access_token_if_needed()
        url = f"{BATCH_RECORDS}"
        url = url.replace(":app_token", app_token).replace(":table_id", table_id)
        req_body = {"record_ids": record_ids}
        resp = await self.req_feishu_api("POST", url=url, req_body=req_body)
        return resp.get("data")

    async def update_bitable_record(self, app_token, table_id, fields={}, record_id=None, **kwargs):
        """
        更新或新增多维表格记录
        """
        await self._authorize_tenant_access_token_if_needed()
        data = {'fields': fields}
        url = f"{lark_host}{BITABLE_RECORDS}"
        url = url.replace(":app_token", app_token).replace(":table_id", table_id)
        method = "POST"  # 新增记录
        if record_id:
            url = f"{url}/{record_id}"
            method = "PUT"  # 更新记录
        resp = await self.req_feishu_api(method, url=url, req_body=data)
        return resp.get("data")

    async def close(self):
        """
        关闭异步客户端
        """
        if self.client:
            await self.client.aclose()