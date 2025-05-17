import traceback
from urllib.parse import urlencode
from .const import *
from .exception import LarkException
from ..utils.log import logger
from .FeishuBase import FeishuBase
import httpx
import json
import time
import os
import datetime
import re
from typing import Union, Optional, Dict, Any, BinaryIO


# 本文件实现一些拓展接口，方便使用

class Feishu(FeishuBase):
    def __init__(self, app_id=os.getenv("FEISHU_APP_ID"), app_secret=os.getenv("FEISHU_APP_SECRET"), print_feishu_log=True):
        """
        初始化飞书API客户端
        :param app_id: 飞书应用的APP ID
        :param app_secret: 飞书应用的APP Secret
        :param print_feishu_log: 是否打印飞书API日志
        """
        super().__init__(app_id, app_secret, print_feishu_log)
    async def add_record(self, app_token: str, table_id: str, fields: dict) -> dict:
        """
        新增记录
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param fields: 新记录的字段,key为字段名，value为字段值
        :return: 新增结果
        """
        await self.check_fileds(app_token, table_id, fields)
        fsres = await self.update_bitable_record(app_token, table_id, fields=fields)
        # 将fileds和record_id包在同一层内
        res = {}
        res['record_id'] = fsres.get("record").get('record_id')
        for key, value in fsres.get("record").get('fields', {}).items():
            res[key] = value
        return res

    async def update_record(self, app_token: str, table_id: str, record_id: str, fields: dict) -> dict:
        """
        更新记录
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param record_id: 记录ID
        :param fields: 更新记录的字段,key为字段名，value为字段值
        :return: 更新结果
        """
        await self.check_fileds(app_token, table_id, fields)
        # 检查记录是否存在
        is_record_exist = False
        try:
            record = await self.bitable_record(app_token, table_id, record_id)
            is_record_exist = True
        except Exception as e:
            # 如果不是记录不存在，则抛出异常
            if not "RecordIdNotFound" in str(e):
                raise e
        if is_record_exist:
            res = await self.update_bitable_record(app_token, table_id, record_id=record_id, fields=fields)
        else:
            res = await self.update_bitable_record(app_token, table_id, fields=fields)
        # 将record_id取外一层
        res['record_id'] = res.get("record").get('record_id')
        return res

    async def check_fileds(self, app_token: str, table_id: str, fields: dict) -> None:
        """
        检查是否包含特定字段，没有则创建
        兼容字段类型，目前只有时间会去兼容
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param fields: 更新字段
        """
        origin_fileds = await self.get_tables_fields(app_token, table_id)

        # 创建一个要删除的键的列表，避免在迭代过程中修改字典
        keys_to_remove = []

        # 创建一个要更新的值的字典
        values_to_update = {}

        for key, value in fields.items():
            # 不存在字段，创建
            if key not in origin_fileds:
                # 根据value选择不同的type
                field_type = 1  # 默认为文本类型

                # 判断是否为日期类型
                if "时间" == key or "日期" == key or key.endswith("时间") or key.endswith("日期"):
                    field_type = 5  # 日期类型
                elif "编号" == key or "自动编号" == key:
                    field_type = 1005  # 自动编号类型
                elif isinstance(value, (int, float)):
                    field_type = 2  # 数字类型
                # 如果值为list[str],则为多选类型
                elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                    field_type = 4  # 多选类型
                # 如果是bool类型，则为复选框类型
                elif isinstance(value, bool):
                    field_type = 7  # 复选框类型

                req_body = {
                    "field_name": key,
                    "type": field_type,
                }
                try:
                    await self.tables_fields(app_token, table_id, req_body=req_body)
                    logger.debug(f"字段 '{key}' 添加成功")
                except Exception as e:
                    logger.error(f"字段添加失败 '{key}': {e}")
            else:
                origin_filed = origin_fileds[key]
                #存在字段，开始兼容
                type = origin_filed.get('type')
                #日期，填写毫秒级时间戳
                if type == 5:
                    # 判断输入类型
                    if isinstance(value, (int, float)):
                        # 将秒数转换为毫秒数，判断范围；大约是 2001 年 9 月 9 日的毫秒级时间戳。
                        if value < 1000000000000:
                            value = int(value * 1000)
                            values_to_update[key] = value
                    elif isinstance(value, str):
                        # 处理空字符串情况
                        if value == "":
                            # 对于空字符串，标记为要删除
                            keys_to_remove.append(key)
                            # 跳过后续处理
                            continue
                        # 将字符串转换为时间戳，支持多种格式
                        elif value == "[NOW]":
                            # 特殊值 [NOW]，使用当前时间
                            value = int(time.time() * 1000)
                            values_to_update[key] = value
                        else:
                            # 尝试多种日期格式
                            formats_to_try = [
                                "%Y-%m-%d %H:%M:%S",  # 标准格式
                                "%Y-%m-%dT%H:%M:%S",  # ISO格式不带毫秒
                                "%Y-%m-%dT%H:%M:%S.%f",  # ISO格式带毫秒
                                "%Y-%m-%d",  # 仅日期
                                "%Y/%m/%d %H:%M:%S",  # 斜杠分隔
                                "%Y/%m/%d"  # 仅日期，斜杠分隔
                            ]
                            converted = False
                            for date_format in formats_to_try:
                                try:
                                    value = int(time.mktime(time.strptime(value, date_format)) * 1000)
                                    converted = True
                                    break  # 成功解析，跳出循环
                                except ValueError:
                                    continue  # 尝试下一个格式

                            # 如果所有格式都失败，但字符串是纯数字，可能已经是时间戳
                            if not converted and isinstance(value, str) and value.isdigit():
                                timestamp = int(value)
                                # 检查是否是秒级时间戳（10位数）
                                if len(value) == 10:
                                    value = timestamp * 1000
                                # 如果是毫秒级时间戳（13位数），直接使用
                                elif len(value) == 13:
                                    value = timestamp
                                converted = True

                            if converted:
                                values_to_update[key] = value
                            else:
                                logger.debug(f"日期格式错误，无法转换: {value}")
                                # 对于无法转换的日期，标记为要删除
                                keys_to_remove.append(key)
                                # 跳过后续处理
                                continue
                    elif isinstance(value, datetime.datetime):
                        value = int(value.timestamp() * 1000)
                        values_to_update[key] = value
                    elif value is None:
                        # 对于None值，标记为要删除
                        keys_to_remove.append(key)
                        # 跳过后续处理
                        continue
                elif type==17:
                    #附件，自动把url或者二进制内容或者文件路径转为file_token
                    try:
                        # 将value转换为列表，如果不是列表的话
                        if not isinstance(value, list):
                            value = [value]

                        file_tokens = []
                        for item in value:
                            file_token = await self._convert_to_file_token(item, app_token, table_id)
                            if file_token:
                                file_tokens.append(file_token)

                        # 确保附件字段的值是列表格式，即使只有一个附件
                        if file_tokens:
                            # 飞书附件字段要求值必须是对象列表
                            values_to_update[key] = file_tokens
                            logger.debug(f"附件字段 '{key}' 转换成功: {file_tokens}")
                        else:
                            # 如果没有有效的文件令牌，标记为要删除
                            keys_to_remove.append(key)
                    except Exception as e:
                        logger.error(f"附件转换失败: {e}\n{traceback.format_exc()}")
                        # 转换失败时，标记为要删除
                        keys_to_remove.append(key)

        # 应用所有更新
        for key, value in values_to_update.items():
            fields[key] = value

        # 删除所有标记为要删除的键
        for key in keys_to_remove:
            if key in fields:
                fields.pop(key)

        # 移除value=None或者""的，不必要上传
        # 注意：日期字段(type=5)的空值已在上面的逻辑中处理，这里是对其他类型字段的处理
        fields = {k: v for k, v in fields.items() if v is not None and v != ""}

    async def get_tables_fields(self, app_token: str, table_id: str) -> dict:
        """
        获取多维表格字段信息
        :param app_token: 多维表格的app_token
        :param table_id: 表格ID
        :return: 字段信息字典，key为字段名，value为字段信息
        """
        try:
            res = await self.tables_fields(app_token, table_id)
            items = res.get('items', [])
            if not items:
                return {}
            fields = {}
            for item in items:
                fields[item.get('field_name')] = item
            return fields
        except Exception as e:
            errmsg = f"获取字段失败 {e}\n{traceback.format_exc()}"
            logger.error(errmsg)
            return {}

    async def clone_fields(self, dest_base_id: str, dest_table_id: str, source_base_id: str, source_table_id: str) -> bool:
        """
        克隆源表格的字段到目标表格
        :param dest_base_id: 目标多维表格的app_token
        :param dest_table_id: 目标表格ID
        :param source_base_id: 源多维表格的app_token
        :param source_table_id: 源表格ID
        :return: 是否克隆成功
        """
        #忽略的ui_type
        ignore_ui_type = [
            "SingleLink",#单项关联
            "Lookup",#查找引用
        ]
        try:
            source_fields = await self.get_tables_fields(source_base_id, source_table_id)
            dest_fields = await self.get_tables_fields(dest_base_id, dest_table_id)

            # 过滤掉ignore_ui_type的源字段
            source_fields = {k: v for k, v in source_fields.items() if v.get('ui_type') not in ignore_ui_type}
            # 过滤掉ignore_ui_type的目标字段
            dest_fields = {k: v for k, v in dest_fields.items() if v.get('ui_type') not in ignore_ui_type}

            # 遍历源字段
            for key, value in source_fields.items():
                req_body = {
                    "field_name": value.get('field_name'),
                    "type": value.get('type'),
                }
                req_body['ui_type'] = value.get('ui_type', None)
                req_body['property'] = None
                status = "添加字段"  # 用于给报错的状态

                try:
                    if key not in dest_fields:  # 添加字段
                        # 处理选项，第一次处理，有id删除
                        if value.get('property', None):
                            req_body['property'] = value.get('property')
                            for option in req_body.get('property', {}).get('options', []):
                                if option.get('id', None):
                                    del option['id']
                        res = await self.tables_fields(app_token=dest_base_id, table_id=dest_table_id, req_body=req_body)
                        logger.info(f"添加字段成功: {res}")
                    else:  # 编辑字段
                        status = "编辑字段"
                        dest_fields_copy = json.loads(json.dumps(dest_fields[key]))
                        # 合并可能存在的原来的property 的 options 到 req_body，判断如果有name重复就跳过，没有才新增
                        if value.get('property', None):
                            if dest_fields[key].get('property', None):
                                # 先把原本的加进来
                                req_body['property'] = dest_fields[key].get('property', None)
                                for option in value.get('property', {}).get('options', []):
                                    if option.get('name', None) in [i.get('name') for i in dest_fields[key].get('property', {}).get('options', [])]:
                                        continue
                                    if option.get('id', None):
                                        del option['id']
                                    req_body['property']['options'].append(option)
                            else:
                                req_body['property'] = value.get('property')
                                for option in req_body.get('property', {}).get('options', []):
                                    if option.get('id', None):
                                        del option['id']

                        # 深拷贝dest_fields
                        remain_list = ['field_name', 'type', 'ui_type', 'property']
                        # 如果没有key，设置None
                        for k in remain_list:
                            if k not in dest_fields_copy:
                                dest_fields_copy[k] = None
                        # 删除没有的字段
                        keys_to_delete = [k for k in dest_fields_copy if k not in remain_list]
                        for k in keys_to_delete:
                            del dest_fields_copy[k]

                        origin = json.dumps(dest_fields_copy, sort_keys=True, ensure_ascii=False)
                        updated = json.dumps(req_body, sort_keys=True, ensure_ascii=False)

                        if origin == updated:
                            continue

                        field_id = dest_fields[key].get('field_id')
                        res = await self.tables_fields(app_token=dest_base_id, table_id=dest_table_id, field_id=field_id, req_body=req_body)
                        logger.info(f"更新字段成功: {res}")

                except Exception as e:
                    errmsg = f"克隆字段失败 {status} dest:{dest_base_id} {dest_table_id} source:{source_base_id} {source_table_id} \n{e}\n{traceback.format_exc()}"
                    if status == "编辑字段":
                        errmsg = f"{errmsg}\n对比前后字段 origin:```{origin}```\nupdated:```{updated}```"
                    logger.error(errmsg)

            return True

        except Exception as e:
            logger.error(f"克隆字段过程中发生错误: {e}\n{traceback.format_exc()}")
            return False
    async def get_all_records(self, app_token: str, table_id: str, req_body: dict = {}) -> list[dict]:
        """
        查询所有记录
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param req_body: 筛选条件
        :return: 记录数据列表
        """
        page_token = ""
        return_data = []
        has_more = True

        while has_more:
            param = {'page_size': 500}
            if page_token:
                param['page_token'] = page_token

            try:
                res = await self.bitable_records_search(app_token, table_id, param=param, req_body=req_body)
                logger.debug(f"查询记录: {res}")
            except Exception as e:
                logger.error(f"查询记录失败: {str(e)}")
                return return_data

            page_token = res.get('page_token', "")
            has_more = res.get('has_more', False)
            items = res.get('items', [])

            if not items:
                return return_data

            for item in items:
                record_id = item.get('record_id')
                fields = item.get('fields', {})
                return_data.append({'record_id': record_id, 'fields': fields})

        return return_data
    async def get_record(self, app_token: str, table_id: str, req_body: dict = {}) -> dict:
        """
        查询单条记录
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param req_body: 筛选条件
        :return: 记录数据字典
        """
        return_data = {}
        try:
            res = await self.bitable_records_search(app_token, table_id, req_body=req_body)
            logger.debug(f"查询记录: {res}")
        except Exception as e:
            logger.error(f"查询记录失败: {str(e)}")
            return return_data
        items = res.get('items', [])
        if not items:
            return return_data
        if len(items) == 0:
            return return_data
        record_id = items[0].get('record_id')
        fields = items[0].get('fields', {})
        total = res.get('total', 0)
        return_data = {'record_id': record_id, 'fields': fields, 'total':total}
        return return_data
    async def get_record_by_id(self, app_token: str, table_id: str, record_id: str) -> dict:
        """
        根据record_id查询单条记录
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param record_id: 记录ID
        :return: 记录数据字典
        """
        try:
            res = await self.bitable_record(app_token, table_id, record_id)
            return res.get('record', {})
        except Exception as e:
            logger.error(f"查询记录失败: {str(e)}")
            return {}

    async def get_records_by_key(self, app_token: str, table_id: str, field_name: str, value: str, sort:list=[]) -> list[dict]:
        """
        根据关键字查询多条记录
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param field_name: 字段名
        :param value: 字段值
        :return: 记录数据列表
        """
        condition = {
            "field_name": field_name,
            "operator": "is",
            "value": [value]
        }
        req_body = {
            "filter": {
                "conjunction": "and",
                "conditions": [condition]
            },
            "sort": sort,
            "automatic_fields": True
        }
        return await self.get_all_records(app_token, table_id, req_body)
    async def get_records_by_record_ids(self, app_token: str, table_id: str, record_ids: list[str]) -> list[dict]:
        """
        根据record_id查询多条记录
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param record_ids: record_id列表
        :return: 记录数据列表
        """
        res = await self.batch_get_records(app_token, table_id, record_ids)
        records = res.get('records', [])
        return_data = []
        for record in records:
            record_id = record.get('record_id')
            fields = record.get('fields', {})
            return_data.append({'record_id': record_id, 'fields': fields})
        return return_data

    async def get_record_by_key(self, app_token: str, table_id: str, field_name: str, value: str, sort:list=[]) -> dict:
        """
        根据关键字查询单条记录
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param field_name: 关键字字段名
        :param value: 关键字值
        :return: 记录数据字典
        """
        condition = {
            "field_name": field_name,
            "operator": "is",
            "value": [value]
        }
        req_body = {
            "filter": {
                "conjunction": "and",
                "conditions": [condition]
            },
            "sort": sort,
            "automatic_fields": True
        }
        res = await self.bitable_records_search(app_token, table_id, req_body=req_body)
        items = res.get('items', [])
        if not items:
            return {}
        record_id = items[0].get('record_id')
        fields = items[0].get('fields', {})
        total = res.get('total', 0)
        return {'record_id': record_id, 'fields': fields, 'total':total}

    async def copy_bitable(self, app_token: str, name: str = None, folder_token: str = None,
                          without_content: bool = False, time_zone: str = "Asia/Shanghai") -> dict:
        """
        复制多维表格

        :param app_token: 要复制的多维表格 App 的唯一标识
        :param name: 多维表格 App 的名称，可选。如果不指定，将使用原表格名称
        :param folder_token: 目标文件夹的 token，可选。如果指定，则复制到该文件夹下
        :param without_content: 是否复制多维表格中的内容，默认 False（复制内容）
                              True: 不复制内容
                              False: 复制内容
        :param time_zone: 文档时区，默认 "Asia/Shanghai"
        :return: 复制后的多维表格信息，包含 app_token 等

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app/copy
        """
        try:
            result = await super().copy_bitable(
                app_token=app_token,
                name=name,
                folder_token=folder_token,
                without_content=without_content,
                time_zone=time_zone
            )

            if self.print_feishu_log:
                logger.info(f"复制多维表格成功: {result}")

            return result
        except Exception as e:
            logger.error(f"复制多维表格失败: {e}\n{traceback.format_exc()}")
            raise


    def _determine_parent_type(self, file_name: str, content_type: str = None) -> str:
        """
        根据文件名或MIME类型确定适合的parent_type

        :param file_name: 文件名
        :param content_type: MIME类型（可选）
        :return: 适合的parent_type，默认为"bitable_file"
        """
        # 图片扩展名列表
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"]

        # 检查文件扩展名
        file_ext = os.path.splitext(file_name.lower())[1]
        if file_ext in image_extensions:
            return "bitable_image"  # 新版文档图片

        # 如果提供了MIME类型，也检查它
        if content_type and content_type.startswith("image/"):
            return "bitable_image"  # 新版文档图片

        # 默认使用bitable_file
        return "bitable_file"  # 新版文档文件

    async def _convert_to_file_token(self, value: Union[str, bytes], app_token: str, table_id: str) -> Optional[Dict[str, Any]]:
        """
        将URL、二进制内容或文件路径转换为飞书文件token

        :param value: URL、二进制内容或文件路径
        :param app_token: 应用Token
        :param table_id: 表格ID
        :return: 文件token字典，包含 file_token 和其他元数据

        注意：会根据文件扩展名或MIME类型自动选择适合的parent_type（bitable_image或bitable_file）
        """
        try:
            # 如果已经是文件token字典，直接返回
            if isinstance(value, dict) and 'file_token' in value:
                return value

            file_name = None
            file_content = None
            content_type = None

            # 判断是URL、二进制内容还是文件路径
            if isinstance(value, str):
                # 检查是否是URL
                url_pattern = re.compile(r'^https?://\S+$')
                if url_pattern.match(value):
                    # 下载URL内容
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(value)
                        response.raise_for_status()
                        file_content = response.content

                        # 获取内容类型
                        content_type = response.headers.get('content-type', '')

                        # 尝试从响应头或URL中提取文件名
                        content_disposition = response.headers.get('content-disposition')
                        if content_disposition and 'filename=' in content_disposition:
                            file_name = re.findall(r'filename="?([^"]+)"?', content_disposition)[0]
                        else:
                            # 从 URL 中提取文件名
                            file_name = os.path.basename(value.split('?')[0])

                        if not file_name or file_name == '':
                            # 生成随机文件名
                            file_ext = ''
                            if '/' in content_type:
                                file_ext = '.' + content_type.split('/')[-1]
                            file_name = f"download_{int(time.time())}{file_ext}"
                else:
                    # 假设是文件路径
                    if os.path.exists(value):
                        with open(value, 'rb') as f:
                            file_content = f.read()
                        file_name = os.path.basename(value)
                    else:
                        logger.error(f"文件不存在: {value}")
                        return None
            elif isinstance(value, bytes):
                # 直接使用二进制内容
                file_content = value
                # 生成随机文件名
                file_name = f"file_{int(time.time())}.bin"
            else:
                logger.error(f"不支持的值类型: {type(value)}")
                return None

            # 上传文件到飞书
            if file_content and file_name:
                # 构建附件的extra参数，指定表格权限
                extra = {"bitablePerm": {"tableId": table_id, "rev": 5}}

                # 确定适合的parent_type
                parent_type = self._determine_parent_type(file_name, content_type)

                try:
                    # 上传文件
                    result = await self.upload_media(
                        file_content=file_content,
                        file_name=file_name,
                        parent_type=parent_type,  # 根据文件类型自动选择
                        parent_node=app_token,  # 使用app_token
                        extra=extra
                    )
                except Exception as e:
                    # 如果使用空间ID失败，尝试使用其他方式
                    logger.warning(f"使用空间ID上传失败，尝试使用默认方式: {e}")
                    # 尝试使用默认的上传方式
                    result = await self.upload_media(
                        file_content=file_content,
                        file_name=file_name,
                        parent_type=parent_type,  # 根据文件类型自动选择
                        parent_node="u-_PbYgUBo",  # 使用固定的默认空间ID
                        extra=extra
                    )

                if result and 'file_token' in result:
                    # 构建飞书附件格式的返回值
                    return {
                        "file_token": result['file_token'],
                        "name": file_name,
                        "size": len(file_content),
                        "type": content_type or "application/octet-stream"  # 使用检测到的MIME类型或默认值
                    }

            return None
        except Exception as e:
            logger.error(f"转换文件token失败: {e}\n{traceback.format_exc()}")
            return None
