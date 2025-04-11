import yaml

from datetime import datetime
import json
from .Feishu import Feishu
from ..utils.log import logger

#飞书模型基类
class BaseModel:
    def __init__(self, app_id: str, app_secret: str, app_token: str, table_id: str):
        self.app_id: str = app_id
        self.app_secret: str = app_secret
        self.app_token: str = app_token
        self.table_id: str = table_id
        self.feishu = Feishu(app_id, app_secret)

    async def get_all_records(self, filter: dict = {}):
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
    async def get_records_by_record_ids(self, record_ids: list[str]) -> list[dict]:
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

    async def get_record_by_record_id(self, record_id: str) -> dict:
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
    async def get_records_by_key(self, filed_name: str, value: str) -> list[dict]:
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
    async def get_record_by_key(self, filed_name: str, value: str) -> dict:
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
    async def add_record(self, fields: dict) -> dict:
        """
        新增记录
        :param fields: 新增字段
        :return: 新增结果
        """
        await self.check_fileds(fields)
        res = await self.feishu.update_bitable_record(self.app_token, self.table_id, fields=fields)
        return res
    async def update_record(self, record_id: str, fields: dict) -> dict:
        """
        更新记录
        :param record_id: record_id
        :param fields: 更新字段
        :return: 更新结果
        """
        await self.check_fileds(fields)
        res = await self.feishu.update_bitable_record(self.app_token, self.table_id, record_id=record_id, fields=fields)
        return res
    async def check_fileds(self, fields: dict) -> None:
        """
        检查是否包含特定字段，没有则创建
        :param fields: 更新字段
        """
        origin_fileds = await self.feishu.get_tables_fields(self.app_token, self.table_id)
        for key, value in fields.items():
            if key not in origin_fileds:
                #需要根据value来选择不同的type
                #1：文本2：数字，暂时只支持这两种
                req_body = {
                    "field_name": key,
                    "type": 1 if isinstance(value, str) else 2,
                }
                try:
                    await self.feishu.tables_fields(self.app_token, self.table_id, req_body=req_body)
                    logger.debug(f"字段 '{key}'添加成功")
                except Exception as e:
                    logger.error(f"字段添加失败 '{key}': {e}")
    # 构造数据表返回元素
    def data_filed2dict(self, fields: dict[str, any], record_id: str) -> dict:
        pass
    # 通用字段转换
    def filed2records(self, fileds: dict[str, any], key: str) -> list[str]:
        value = fileds.get(key, {})
        if "link_record_ids" in value:
            return value.get("link_record_ids")
        return []

    def filed2float(self, fileds: dict[str, any], key: str) -> float:
        value = fileds.get(key, [])
        if isinstance(value, (int, float)):
            return float(value)
        return 1

    def filed2text(self, fileds: dict[str, any], key: str) -> str:
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

    def filed_json2list(self, fileds: dict[str, any], key: str) -> list[any]:
        json_data = self.filed2text(fileds, key)
        try:
            return json.loads(json_data)
        except:
            return []

    def filed_yml2list(self, fileds: dict[str, any], key: str) -> list[any]:
        yml_data = self.filed2text(fileds, key)
        try:
            return yaml.safe_load(yml_data)
        except:
            return []

    def filed_yml2dict(self, fileds: dict[str, any], key: str) -> dict:
        yml_data = self.filed2text(fileds, key)
        try:
            return yaml.safe_load(yml_data)
        except:
            return {}

    #构造条件筛选
    def build_condition(self, condition: dict[str, str]) -> str:
        condition_list = []
        for key, value in condition.items():
            condition_list.append(f"{key} = '{value}'")
        return " and ".join(condition_list)

    # 构造飞书多维表格筛选条件
    def build_filter_condition(self, field_name: str, operator: str, value: any) -> dict:
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

    def build_and_filter(self, conditions: list[dict]) -> dict:
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

    def build_or_filter(self, conditions: list[dict]) -> dict:
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

    def build_complex_filter(self, children: list[dict], conjunction: str = "and") -> dict:
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
