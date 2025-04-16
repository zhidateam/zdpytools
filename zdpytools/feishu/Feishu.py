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
        :param fields: 新增字段
        :return: 新增结果
        """
        await self.check_fileds(app_token, table_id, fields)
        res = await self.update_bitable_record(app_token, table_id, fields=fields)
        return res

    async def update_record(self, app_token: str, table_id: str, record_id: str, fields: dict) -> dict:
        """
        更新记录
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param record_id: 记录ID
        :param fields: 更新字段
        :return: 更新结果
        """
        await self.check_fileds(app_token, table_id, fields)
        res = await self.update_bitable_record(app_token, table_id, record_id=record_id, fields=fields)
        return res

    async def check_fileds(self, app_token: str, table_id: str, fields: dict) -> None:
        """
        检查是否包含特定字段，没有则创建
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param fields: 更新字段
        """
        origin_fileds = await self.get_tables_fields(app_token, table_id)
        for key, value in fields.items():
            if key not in origin_fileds:
                # 根据value选择不同的type
                field_type = 1  # 默认为文本类型

                # 判断是否为日期类型
                if (isinstance(value, int) and len(str(value)) == 13) or \
                   (isinstance(value, str) and (value.startswith("20") or value == "[NOW]")) or \
                   "时间" in key or "日期" in key:
                    field_type = 5  # 日期类型
                elif isinstance(value, (int, float)):
                    field_type = 2  # 数字类型

                req_body = {
                    "field_name": key,
                    "type": field_type,
                }
                try:
                    await self.tables_fields(app_token, table_id, req_body=req_body)
                    logger.debug(f"字段 '{key}' 添加成功")
                except Exception as e:
                    logger.error(f"字段添加失败 '{key}': {e}")


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
    async def get_all_records(self, app_token: str, table_id: str, filter: dict = {}) -> list[dict]:
        """
        查询所有记录
        :param app_token: 应用Token
        :param table_id: 表格ID
        :param filter: 筛选条件
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
                res = await self.bitable_records_search(app_token, table_id, param=param, req_body=filter)
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

    async def get_records_by_key(self, app_token: str, table_id: str, field_name: str, value: str) -> list[dict]:
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
        filter = {
            "filter": {
                "conjunction": "and",
                "conditions": [condition]
            }
        }
        return await self.get_all_records(app_token, table_id, filter)
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

    async def get_record_by_key(self, app_token: str, table_id: str, field_name: str, value: str) -> dict:
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
        filter = {
            "filter": {
                "conjunction": "and",
                "conditions": [condition]
            }
        }
        res = await self.bitable_records_search(app_token, table_id, req_body=filter)
        items = res.get('items', [])
        if not items:
            return {}
        record_id = items[0].get('record_id')
        fields = items[0].get('fields', {})
        return {'record_id': record_id, 'fields': fields}
