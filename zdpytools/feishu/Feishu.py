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
        super().__init__(app_id, app_secret, print_feishu_log)

    async def get_tables_fields(self, app_token: str, table_id: str) -> dict:
        """
        获取多维表格字段作为字典，key是字段名字，value是字段信息
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
