import yaml

from datetime import datetime
import json
from .Feishu import Feishu
from ..utils.log import logger

#飞书模型基类
class BaseModel:
    def __init__(self, app_id, app_secret, app_token, table_id):
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
        self.table_id = table_id
        self.feishu = Feishu(app_id, app_secret)

    async def get_all_records(self,filter:dict={}):
        """
        查询所有记录
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
                res = await self.feishu.bitable_records_search(self.app_token, self.table_id, param=param,req_body=filter)
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
                data = self.data_filed2dict(fields, record_id)
                if data:
                    return_data.append(data)

        return return_data
    async def get_records_by_record_ids(self, record_ids: list):
        """
        根据record_id查询多条记录
        :param record_ids: record_id列表
        :return: 记录数据列表
        """
        res = await self.feishu.batch_get_records(self.app_token, self.table_id, record_ids)
        records = res.get('records', [])
        return_data = []
        for record in records:
            record_id = record.get('record_id')
            fields = record.get('fields', {})
            data = self.data_filed2dict(fields, record_id)
            if data:
                return_data.append(data)
        return return_data

    async def get_record_by_record_id(self, record_id):
        """
        根据record_id查询单条记录
        :param record_id: record_id
        :return: 记录数据字典
        """
        res = await self.feishu.bitable_record(self.app_token, self.table_id, record_id)
        fields = res.get('record', {}).get('fields', {})
        if not fields:
            return {}
        return self.data_filed2dict(fields, record_id)
    async def get_records_by_key(self, filed_name, value):
        """
        根据关键字查询多条记录
        :param filed_name: 关键字字段名
        :param value: 关键字值
        :return: 记录数据列表
        """
        condition = self.build_filter_condition(filed_name, "is", value)
        filter = self.build_and_filter([condition])
        res = await self.get_all_records(filter)
        return res
    async def get_record_by_key(self, filed_name, value):
        """
        根据关键字查询单条记录
        :param filed_name: 关键字字段名
        :param value: 关键字值
        :return: 记录数据字典
        """
        condition = self.build_filter_condition(filed_name, "is", value)
        filter = self.build_and_filter([condition])
        res = await self.feishu.bitable_records_search(self.app_token, self.table_id, req_body=filter)
        items = res.get('items', [])
        if not items:
            return {}
        record_id = items[0].get('record_id')
        fields = items[0].get('fields', {})
        return self.data_filed2dict(fields, record_id)
    async def update_record(self, record_id, fields):
        """
        更新记录
        :param record_id: record_id
        :param fields: 更新字段
        :return: 更新结果
        """
        res = await self.feishu.update_bitable_record(self.app_token, self.table_id, record_id=record_id, fields=fields)
        return res
    # 构造数据表返回元素
    def data_filed2dict(self, fields: dict, record_id: str) -> dict:
        pass
    # 通用字段转换
    def filed2records(self, fileds: dict, key: str) -> list:
        value = fileds.get(key, {})
        if "link_record_ids" in value:
            return value.get("link_record_ids")
        return []

    def filed2float(self, fileds: dict, key: str) -> float:
        value = fileds.get(key, [])
        if isinstance(value, (int, float)):
            return float(value)
        return 1

    def filed2text(self, fileds: dict, key: str) -> str:
        res = ""
        value = fileds.get(key, [])
        # 处理嵌套value类型（如url）
        if isinstance(value, dict) and value.get('value'):
            value = value.get('value')
        # 处理整数、浮点数等非可迭代类型
        if isinstance(value, (int, float)):
            #判断如果key包含时间字样
            if "时间" in key:
                try:
                    return datetime.fromtimestamp(value/1000).strftime('%Y-%m-%d %H:%M:%S')
                except (OSError, ValueError, OverflowError) as e:
                    logger.error(f"时间戳转换错误: {value}, 错误: {e}")
                    return str(value)
            return str(value)
        # 处理可迭代类型
        for item in value:
            if isinstance(item, dict):
                if item.get('text', ''):
                    res = f"{res}{item.get('text')}"
            elif isinstance(item, str):
                res = f"{res}{item}"
            elif isinstance(item, (int, float)):
                res = f"{res}{str(item)}"
        return res

    def filed_json2list(self, fileds: dict, key: str) -> list:
        json_data = self.filed2text(fileds, key)
        try:
            return json.loads(json_data)
        except:
            return []

    def filed_yml2list(self, fileds: dict, key: str) -> list:
        yml_data = self.filed2text(fileds, key)
        try:
            return yaml.safe_load(yml_data)
        except:
            return []

    def filed_yml2dict(self, fileds: dict, key: str) -> dict:
        yml_data = self.filed2text(fileds, key)
        try:
            return yaml.safe_load(yml_data)
        except:
            return {}

    #构造条件筛选
    def build_condition(self, condition: dict) -> dict:
        condition_list = []
        for key, value in condition.items():
            condition_list.append(f"{key} = '{value}'")
        return " and ".join(condition_list)

    # 构造飞书多维表格筛选条件
    def build_filter_condition(self, field_name: str, operator: str, value) -> dict:
        """
        构造单个筛选条件

        参数:
            field_name: 字段名称
            operator: 操作符，可选值包括 is, isNot, contains, doesNotContain, isEmpty, isNotEmpty,
                      isGreater, isGreaterEqual, isLess, isLessEqual
            value: 筛选值，可以是单个值或列表

        返回:
            dict: 单个筛选条件的字典
        """
        # 确保value是列表类型
        if not isinstance(value, list):
            value = [value]

        # 对于isEmpty和isNotEmpty操作符，value应为空列表
        if operator in ['isEmpty', 'isNotEmpty']:
            value = []

        return {
            "field_name": field_name,
            "operator": operator,
            "value": value
        }

    def build_and_filter(self, conditions: list) -> dict:
        """
        构造AND筛选条件

        参数:
            conditions: 筛选条件列表，每个条件是通过build_filter_condition构造的字典

        返回:
            dict: 完整的AND筛选条件
        """
        return {
            "filter": {
                "conjunction": "and",
                "conditions": conditions
            }
        }

    def build_or_filter(self, conditions: list) -> dict:
        """
        构造OR筛选条件

        参数:
            conditions: 筛选条件列表，每个条件是通过build_filter_condition构造的字典

        返回:
            dict: 完整的OR筛选条件
        """
        return {
            "filter": {
                "conjunction": "or",
                "conditions": conditions
            }
        }

    def build_complex_filter(self, children: list, conjunction: str = "and") -> dict:
        """
        构造复杂筛选条件，支持嵌套的AND/OR逻辑

        参数:
            children: 子筛选条件列表，每个子条件可以是AND或OR筛选
            conjunction: 顶层连接词，"and"或"or"

        返回:
            dict: 完整的复杂筛选条件
        """
        return {
            "filter": {
                "conjunction": conjunction,
                "children": children
            }
        }
