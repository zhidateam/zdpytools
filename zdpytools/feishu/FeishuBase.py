from typing import Optional, Union, BinaryIO, Dict, Any
from urllib.parse import urlencode
from .const import *
from .exception import LarkException
from ..utils.log import logger
import httpx
import json
import time
import os
import io


# 本文件仅实现飞书原版接口调用，不进行进一步封装

class FeishuBase:
    def __init__(self, app_id: str = os.getenv("FEISHU_APP_ID"), app_secret: str = os.getenv("FEISHU_APP_SECRET"), print_feishu_log: bool = True):
        print(app_id, app_secret)
        if not app_id or not app_secret:
            raise ValueError("app_id 或 app_secret 为空")
        self._app_id = app_id
        self._app_secret = app_secret
        self.print_feishu_log = print_feishu_log
        self._tenant_access_token = ""
        self._token_expire_time = 0  # 记录token过期时间
        self.client = httpx.AsyncClient(timeout=10.0)

    def _is_token_expired(self) -> bool:
        """
        检查当前 token 是否过期
        """
        # 提前5分钟刷新 token，避免正好在过期边缘
        return time.time() >= (self._token_expire_time - 300)

    async def _authorize_tenant_access_token(self) -> None:
        """
        使用 httpx 异步请求获取 tenant_access_token
        """
        url = f"{FEISHU_HOST}{TENANT_ACCESS_TOKEN_URI}"
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

    async def _authorize_tenant_access_token_if_needed(self) -> None:
        """
        如果没有 token 或 token 已过期，则获取新 token
        """
        if not self._tenant_access_token or self._is_token_expired():
            await self._authorize_tenant_access_token()

    async def req_feishu_api(self, method: str, url: str, req_body: dict = None, check_code: bool = True, check_status: bool = True) -> dict:
        """
        发起飞书 API 异步请求
        """
        await self._authorize_tenant_access_token_if_needed()

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self._tenant_access_token,
        }

        if self.print_feishu_log:
            logger.debug(f"{method} 请求飞书接口: {url}")
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

    async def bitable_records_search(self, app_token: str, table_id: str, param: dict = {}, req_body: dict = {}, **kwargs) -> dict:
        """
        根据条件查询多维表格记录
        """
        url = f"{FEISHU_HOST}{BITABLE_RECORDS_SEARCH}"
        url = url.replace(":app_token", app_token).replace(":table_id", table_id)
        if param:
            url = url + "?" + urlencode(param)
        resp = await self.req_feishu_api("POST", url=url, req_body=req_body)
        return resp.get("data")

    async def bitable_record(self, app_token: str, table_id: str, record_id: str, **kwargs) -> dict:
        """
        根据 record_id 查询单条记录
        """
        url = f"{FEISHU_HOST}{BITABLE_RECORD}"
        url = url.replace(":app_token", app_token).replace(":table_id", table_id).replace(":record_id", record_id)
        resp = await self.req_feishu_api("GET", url=url)
        return resp.get("data")

    async def batch_get_records(self, app_token: str, table_id: str, record_ids: list[str], **kwargs) -> dict:
        """
        批量获取多维表格记录
        """
        url = f"{BATCH_RECORDS}"
        url = url.replace(":app_token", app_token).replace(":table_id", table_id)
        req_body = {"record_ids": record_ids, "automatic_fields": True}
        resp = await self.req_feishu_api("POST", url=url, req_body=req_body)
        return resp.get("data")

    async def update_bitable_record(self, app_token: str, table_id: str, fields: dict = {}, record_id: str = None, **kwargs) -> dict:
        """
        更新或新增多维表格记录
        """
        data = {'fields': fields}
        url = f"{FEISHU_HOST}{BITABLE_RECORDS}"
        url = url.replace(":app_token", app_token).replace(":table_id", table_id)
        method = "POST"  # 新增记录
        if record_id:
            url = f"{url}/{record_id}"
            method = "PUT"  # 更新记录
        resp = await self.req_feishu_api(method, url=url, req_body=data)
        return resp.get("data")

    async def close(self) -> None:
        """
        关闭异步客户端
        """
        if self.client:
            await self.client.aclose()

    async def upload_media(self, file_path: str = None, file_content: bytes = None, file_name: str = None,
                          parent_type: str = "bitable_image", parent_node: str = None,
                          extra: Optional[Union[str, Dict[str, Any]]] = None) -> dict:
        """
        上传素材到飞书云文档

        :param file_path: 文件路径，与file_content二选一
        :param file_content: 文件内容的二进制数据，与file_path二选一
        :param file_name: 文件名称，如果使用file_path且未提供file_name，则使用file_path的文件名
        :param parent_type: 上传点类型，可选值包括：
                          - doc_image：旧版文档图片
                          - bitable_image：新版文档图片
                          - sheet_image：电子表格图片
                          - doc_file：旧版文档文件
                          - bitable_file：新版文档文件
        :param parent_node: 上传点的token，即要上传到的云文档token
        :param extra: 额外参数，格式为字典或JSON字符串，例如：{"drive_route_token":"doxcnXgNGAtaAraIRVeCfmabcef"}
        :return: 响应数据，包含file_token

        文档: https://open.feishu.cn/document/server-docs/docs/drive-v1/media/upload_all
        """
        if not file_path and not file_content:
            raise ValueError("必须提供file_path或file_content参数")

        if not parent_node:
            raise ValueError("必须提供parent_node参数")

        # 获取文件内容和文件名
        if file_path:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            if not file_name:
                file_name = os.path.basename(file_path)
        elif not file_name:
            raise ValueError("使用file_content时必须提供file_name参数")

        # 获取文件大小
        file_size = len(file_content)
        if file_size > 20 * 1024 * 1024:  # 20MB
            raise ValueError("文件大小不能超过20MB，请使用分片上传")

        # 构建URL
        url = f"{FEISHU_HOST}{UPLOAD_MEDIA_URI}"

        # 准备授权token
        await self._authorize_tenant_access_token_if_needed()

        # 构建表单数据
        form_data = {
            'file_name': file_name,
            'parent_type': parent_type,
            'parent_node': parent_node,
            'size': str(file_size),
            'file': (file_name, file_content)
        }

        # 添加可选参数
        if extra:
            if isinstance(extra, dict):
                extra = json.dumps(extra)
            form_data['extra'] = extra

        # 使用httpx的files参数处理文件上传
        files = {
            'file': (file_name, file_content, 'application/octet-stream')
        }

        # 移除files中的file键，因为它会在files参数中提供
        form_data_without_file = {k: v for k, v in form_data.items() if k != 'file'}

        headers = {
            "Authorization": "Bearer " + self._tenant_access_token
        }

        if self.print_feishu_log:
            logger.debug(f"POST 请求飞书上传接口: {url}")
            logger.debug(f"表单数据: {form_data_without_file}")

        try:
            response = await self.client.post(url, data=form_data_without_file, files=files, headers=headers)

            if response.status_code != 200:
                logger.error(f"HTTP 状态码异常: {response.status_code}, 响应内容: {response.text}")
                raise LarkException(code=response.status_code, msg="HTTP状态码异常", url=url, req_body=form_data_without_file, headers=headers)

            resp_data = response.json()

            if self.print_feishu_log:
                logger.debug(f"飞书接口响应: {resp_data}")

            if resp_data.get("code", -1) != 0:
                logger.error(f"接口返回错误, URL: {url}, 错误信息: {resp_data}")
                raise LarkException(code=resp_data.get("code"), msg=resp_data.get("msg"), url=url, req_body=form_data_without_file, headers=headers)

            return resp_data.get("data", {})
        except httpx.HTTPError as e:
            logger.error(f"请求飞书上传接口异常: {e}, URL: {url}")
            raise LarkException(code=-1, msg=f"请求失败: {str(e)}", url=url, req_body=form_data_without_file, headers=headers)
        except json.JSONDecodeError as e:
            logger.error(f"解析上传响应 JSON 失败: {e}, URL: {url}")
            raise LarkException(code=-1, msg="响应解析失败", url=url, req_body=form_data_without_file, headers=headers)

    async def batch_get_tmp_download_url(self, file_tokens: list =None, extra: Optional[Union[str, dict]] = None) -> dict:
        """
        获取素材临时下载链接

        参数:
            file_tokens: 文件 token 列表，例如 ["boxcnrHpsg1QDqXAAAyachabcef"]
            extra: 额外参数，可选;参考https://open.feishu.cn/document/server-docs/docs/drive-v1/media/introduction

        返回:
            响应数据:{'tmp_download_urls': [{'file_token': 'X79qbILJwozCPHxmQtVcaeBUnAc', 'tmp_download_url': 'https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=M2I5ODA5ZDVhOWVhYjQ0MDMyZDlkYTI2ZGMwOTE1MjdfYzY3ZmYyYTMwZjJiOGJmNzAzNmZiOWUxYTFkZmUzYzBfSUQ6NzQ5NDg3NTM1NzgyOTU2MjM3MF8xNzQ1MDQ5NzYyOjE3NDUxMzYxNjJfVjM'}]}

        文档: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/media/batch_get_tmp_download_url
        """
        # 使用直接提供的file_tokens和extra
        if not file_tokens:
            raise ValueError("必须提供tmp_urls或file_tokens参数")

        url = f"{FEISHU_HOST}{BATCH_GET_TMP_DOWNLOAD_URL}"

        # 根据文档，file_tokens参数需要多次传递，而不是用逗号连接
        # 构建查询参数，每个token作为单独的file_tokens参数
        params = []
        for token in file_tokens:
            params.append(("file_tokens", token))

        # 添加extra参数（如果有）
        if extra:
            if isinstance(extra, dict):
                extra = json.dumps(extra)
            params.append(("extra", extra))

        # 使用urllib.parse.urlencode的doseq=True参数来正确处理重复参数
        query_string = urlencode(params, doseq=True)
        url = f"{url}?{query_string}"

        resp = await self.req_feishu_api("GET", url=url)
        return resp.get("data")

    async def tables_fields(self, app_token: str, table_id: str, query_params: dict = None, field_id: str = "", req_body: dict = None) -> dict:
        self.__dict__.update(locals())
        url = "{}{}".format(
            FEISHU_HOST, TABLES_FIELDS
        ).replace(':app_token', app_token).replace(':table_id', table_id).replace(':field_id', field_id)

        # 如果url是以/结尾的，就去掉
        if url[-1] == '/':
            url = url[:-1]

        if query_params:
            url = url + "?" + urlencode(query_params)

        if not req_body and not field_id:
            action = "GET"
        elif req_body and not field_id:
            action = "POST"
        elif req_body and field_id:
            action = "PUT"
            #更新字段，下面是文档注释
            """
type可选值有：
1：文本
2：数字
3：单选
4：多选
5：日期
7：复选框
11：人员
13：电话号码
15：超链接
17：附件
18：单项关联
20：公式（不支持设置公式表达式）
21：双向关联
22：地理位置
23：群组
1001：创建时间
1002：最后更新时间
1003：创建人
1004：修改人
1005：自动编号

            """
        elif not req_body and field_id:
            action = "DELETE"

        resp = await self.req_feishu_api(action, url=url, req_body=req_body)
        return resp.get('data')

    async def copy_bitable(self, app_token: str, name: str = None, folder_token: str = None,
                          without_content: bool = False, time_zone: str = None) -> dict:
        """
        复制多维表格

        :param app_token: 要复制的多维表格 App 的唯一标识
        :param name: 多维表格 App 的名称，可选
        :param folder_token: 目标文件夹的 token，可选。如果指定，则复制到该文件夹下
        :param without_content: 是否复制多维表格中的内容，默认 False（复制内容）
                              True: 不复制内容
                              False: 复制内容
        :param time_zone: 文档时区，例如 "Asia/Shanghai"，可选
        :return: 响应数据，包含新创建的多维表格信息
        {
        "code": 0,
        "data": {
            "app": {
            "app_token": "KnwLblU5daG9zdsJEGrceYBRntf",
            "default_table_id": "",
            "folder_token": "Dio2fa1WClP8qYdIXkrcpTkhnId",
            "name": "一篇新的多维表格",
            "time_zone": "Asia/Shanghai",
            "url": "https://bcns75ga0lpd.feishu.cn/base/KnwLblU5daG9zdsJEGrceYBRntf"
            }
        },
        "msg": "success"
        }

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app/copy
        """
        url = f"{FEISHU_HOST}{BITABLE_COPY_URI}".replace(":app_token", app_token)

        # 构建请求体
        req_body = {}
        if name:
            req_body["name"] = name
        if folder_token:
            req_body["folder_token"] = folder_token
        if without_content is not None:
            req_body["without_content"] = without_content
        if time_zone:
            req_body["time_zone"] = time_zone

        resp = await self.req_feishu_api("POST", url=url, req_body=req_body)
        return resp.get("data")

    async def batch_create_permissions(self, token: str, members: list, doc_type: str, need_notification: bool = False) -> dict:
        """
        批量添加协作者权限

        :param token: 云文档的 token，需要与 doc_type 参数指定的云文档类型相匹配
        :param members: 本次要增加权限的协作者列表，格式为包含成员信息的字典列表，最多10个成员
                      每个成员字典包含：
                      - member_type: 成员类型，可选值：
                        - email: 邮箱
                        - openid: 开放平台ID
                        - unionid: 统一ID
                        - userid: 用户ID
                        - chat_id: 群组ID
                        - department_id: 部门ID
                      - member_id: 成员ID，与member_type对应
                      - perm: 权限类型，可选值：
                        - view: 可阅读
                        - edit: 可编辑
                        - full_access: 可管理
        :param doc_type: 云文档类型，需要与云文档的 token 相匹配，可选值：
                       - doc：旧版文档
                       - sheet：电子表格
                       - file：云空间文件
                       - wiki：知识库节点
                       - bitable：多维表格
        :param need_notification: 添加权限后是否通知对方，默认 False（不通知）
                                True: 通知
                                False: 不通知
        :return: 响应数据，包含添加结果
        {
            "code": 0,
            "data": {
                "results": [
                    {
                        "member": {
                            "member_id": "ou_7dab8a3d3cdcc9da365777c7ad535d62",
                            "member_type": "openid"
                        },
                        "perm": "view"
                    }
                ]
            },
            "msg": "success"
        }

        文档: https://open.feishu.cn/document/server-docs/docs/drive-v1/permission/members/batch_create
        """
        # 验证参数
        if not token:
            raise ValueError("必须提供token参数")
        if not members or not isinstance(members, list) or len(members) == 0:
            raise ValueError("必须提供members参数，且为非空列表")
        if len(members) > 10:
            raise ValueError("members列表最多包含10个成员")
        if not doc_type:
            raise ValueError("必须提供doc_type参数")

        # 构建URL
        url = f"{FEISHU_HOST}{BATCH_CREATE_PERMISSIONS_URI}".replace(":token", token)

        # 添加查询参数
        params = {"type": doc_type}
        if need_notification is not None:
            params["need_notification"] = str(need_notification).lower()

        # 构建完整URL
        url = f"{url}?{urlencode(params)}"

        # 构建请求体
        req_body = {"members": members}

        # 发送请求
        resp = await self.req_feishu_api("POST", url=url, req_body=req_body)
        return resp.get("data")

    async def list_tables(self, app_token: str, page_token: str = None, page_size: int = None) -> dict:
        """
        列出多维表格中的所有数据表，包括其 ID、版本号和名称。

        :param app_token: 多维表格 App 的唯一标识
        :param page_token: 分页标记，第一次请求不填，表示从头开始遍历；分页查询结果还有更多项时会同时返回新的 page_token
        :param page_size: 分页大小，默认20，最大100
        :return: 响应数据，包含数据表列表
        {
            "code": 0,
            "msg": "success",
            "data": {
                "has_more": false,
                "page_token": "tblKz5D60T4JlfcT",
                "total": 1,
                "items": [
                    {
                        "table_id": "tblKz5D60T4JlfcT",
                        "revision": 1,
                        "name": "数据表1"
                    }
                ]
            }
        }

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table/list
        """
        url = f"{FEISHU_HOST}{BITABLE_TABLES_LIST_URI}".replace(":app_token", app_token)

        # 构建查询参数
        params = {}
        if page_token:
            params["page_token"] = page_token
        if page_size:
            params["page_size"] = page_size

        # 添加查询参数到URL
        if params:
            url = f"{url}?{urlencode(params)}"

        # 发送请求
        resp = await self.req_feishu_api("GET", url=url)
        return resp.get("data")

    async def transfer_owner(self, token: str, member_type: str, member_id: str, doc_type: str,
                            need_notification: bool = True, remove_old_owner: bool = False,
                            stay_put: bool = False, old_owner_perm: str = "full_access") -> dict:
        """
        转移云文档所有者权限

        :param token: 云文档的 token，需要与 doc_type 参数指定的云文档类型相匹配
        :param member_type: 新所有者的 ID 类型，可选值：
                          - email：飞书邮箱
                          - openid：开放平台ID
                          - userid：用户自定义ID
        :param member_id: 新所有者的 ID，与 member_type 对应
        :param doc_type: 云文档类型，需要与云文档的 token 相匹配，可选值：
                       - doc：文档
                       - sheet：电子表格
                       - file：云空间文件
                       - wiki：知识库节点
                       - bitable：多维表格
        :param need_notification: 是否需要通知新的文件所有者，默认 True（通知）
                                True: 通知
                                False: 不通知
        :param remove_old_owner: 转移后是否需要移除原文件所有者的权限，默认 False（不移除）
                               True: 移除
                               False: 不移除
        :param stay_put: 仅当文件在个人文件夹下，此参数才会生效。默认 False（移动到新所有者空间）
                       True: 留在原位置
                       False: 移动到新所有者的空间下
        :param old_owner_perm: 仅当 remove_old_owner = False 时，此参数才会生效
                             保留原文件所有者指定的权限角色，默认 "full_access"（可管理）
                             可选值：
                             - view: 可阅读
                             - edit: 可编辑
                             - full_access: 可管理
        :return: 响应数据，包含转移结果
        {
            "code": 0,
            "data": {},
            "msg": "success"
        }

        文档: https://open.feishu.cn/document/server-docs/docs/drive-v1/permission/members/transfer_owner
        """
        # 验证参数
        if not token:
            raise ValueError("必须提供token参数")
        if not member_type:
            raise ValueError("必须提供member_type参数")
        if not member_id:
            raise ValueError("必须提供member_id参数")
        if not doc_type:
            raise ValueError("必须提供doc_type参数")

        # 验证member_type是否为有效值
        valid_member_types = ["email", "openid", "userid"]
        if member_type not in valid_member_types:
            raise ValueError(f"member_type参数必须为以下值之一: {', '.join(valid_member_types)}")

        # 验证old_owner_perm是否为有效值
        valid_perms = ["view", "edit", "full_access"]
        if old_owner_perm not in valid_perms:
            raise ValueError(f"old_owner_perm参数必须为以下值之一: {', '.join(valid_perms)}")

        # 构建URL
        url = f"{FEISHU_HOST}{TRANSFER_OWNER_URI}".replace(":token", token)

        # 添加查询参数
        params = {"type": doc_type}
        if need_notification is not None:
            params["need_notification"] = str(need_notification).lower()
        if remove_old_owner is not None:
            params["remove_old_owner"] = str(remove_old_owner).lower()
        if stay_put is not None:
            params["stay_put"] = str(stay_put).lower()
        if old_owner_perm and not remove_old_owner:
            params["old_owner_perm"] = old_owner_perm

        # 构建完整URL
        url = f"{url}?{urlencode(params)}"

        # 构建请求体
        req_body = {
            "member_type": member_type,
            "member_id": member_id
        }

        # 发送请求
        resp = await self.req_feishu_api("POST", url=url, req_body=req_body)
        return resp.get("data")
