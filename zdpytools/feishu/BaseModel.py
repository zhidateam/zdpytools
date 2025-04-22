import yaml
import inspect
from datetime import datetime
import json
from .Feishu import Feishu
from ..utils.log import logger

#飞书模型基类
class BaseModel:
    def __init__(self, app_id: str, app_secret: str, app_token: str, table_id: str,async_get_fileds: bool = True):
        self.app_id: str = app_id
        self.app_secret: str = app_secret
        self.app_token: str = app_token
        self.table_id: str = table_id
        self.feishu: Feishu = Feishu(app_id, app_secret)
        self.async_get_fileds:bool = async_get_fileds
    #查询所有记录
    async def get_all_records(self, filter: dict = {}):
        return await self.feishu.get_all_records(self.app_token, self.table_id, filter)
    # 根据record_id查询单条记录
    async def get_record_by_record_id(self, record_id: str) -> dict:
        record = await self.feishu.get_record_by_id(self.app_token, self.table_id, record_id)
        if not record or record == {}:
            return {}
        res = await self.auto_data_filed2dict(record.get('fields'), record.get('record_id'))
        return res
    #根据record_id列表查询多条记录
    async def get_records_by_record_ids(self, record_ids: list[str]) -> list[dict]:
        res = []
        records = await self.feishu.get_records_by_record_ids(self.app_token, self.table_id, record_ids)
        for record in records:
            if not record or record == {}:
                continue
            res.append(await self.auto_data_filed2dict(record.get('fields'), record.get('record_id')))
        return res
    # 根据关键字查询单条记录
    async def get_record_by_key(self, field_name: str, value: str) -> dict:
        record = await self.feishu.get_record_by_key(self.app_token, self.table_id, field_name, value)
        if not record or record == {}:
            return {}
        res = await self.auto_data_filed2dict(record.get('fields'), record.get('record_id'))
        return res
    # 根据关键字查询多条记录，返回列表
    async def get_records_by_key(self, field_name: str, value: str) -> list[dict]:
        res = []
        records = await self.feishu.get_records_by_key(self.app_token, self.table_id, field_name, value)
        for record in records:
            if not record or record == {}:
                continue
            res.append(await self.auto_data_filed2dict(record.get('fields'), record.get('record_id')))
        return res
    # 添加记录
    async def add_record(self, fields: dict) -> dict:
        return await self.feishu.add_record(self.app_token, self.table_id, fields)
    # 更新记录
    async def update_record(self, record_id: str, fields: dict) -> dict:
        return await self.feishu.update_record(self.app_token, self.table_id, record_id, fields)

    # 查询字段
    async def get_tables_fields(self) -> dict:
        return await self.feishu.get_tables_fields(self.app_token, self.table_id)
    # 自动判断使用同步还是异步版本的data_filed2dict
    async def auto_data_filed2dict(self, fileds: dict[str, any], record_id: str) -> dict:
        """
        自动判断使用同步还是异步版本的data_filed2dict
        如果子类实现了异步版本，则使用异步版本；否则使用同步版本
        """
        if self.async_get_fileds:
            #使用异步版本
            return await self.async_data_filed2dict(fileds, record_id)
        else:
            # 使用同步版本
            return self.data_filed2dict(fileds, record_id)

    # --------------给下面继承实现-----------------
    def data_filed2dict(self, fileds: dict[str, any], record_id: str) -> dict:
        """
        同步版本，用于同步获取字段值
        子类应该实现此方法以处理不需要异步操作的字段
        """
        return {'record_id': record_id}

    async def async_data_filed2dict(self, fileds: dict[str, any], record_id: str) -> dict:
        """
        异步版本，用于异步获取字段值
        子类应该实现此方法以处理需要异步操作的字段，如下载链接等
        """
        return {'record_id': record_id}

    #-----------下面为字段转化方法--------------------
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

    async def filed2download_urls(self, fileds: dict[str, any], key: str, table_id:str) -> list[str]:
        """
        value例子：[{'file_token': 'X79qbILJwozCPHxmQtVcaeBUnAc', 'name': 'image.png', 'size': 1669629, 'tmp_url': 'https://open.feishu.cn/open-apis/drive/v1/medias/batch_get_tmp_download_url?file_tokens=X79qbILJwozCPHxmQtVcaeBUnAc&extra=%7B%22bitablePerm%22%3A%7B%22tableId%22%3A%22tbl2sZepp03XykVV%22%2C%22rev%22%3A5%7D%7D', 'type': 'image/png', 'url': 'https://open.feishu.cn/open-apis/drive/v1/medias/X79qbILJwozCPHxmQtVcaeBUnAc/download?extra=%7B%22bitablePerm%22%3A%7B%22tableId%22%3A%22tbl2sZepp03XykVV%22%2C%22rev%22%3A5%7D%7D'}],
        """
        value = fileds.get(key, [])
        if not value:
            return []
        res = []
        #rev暂时不知道作用
        extra = {"bitablePerm":{"tableId":table_id,"rev":5}}
        file_tokens = [item.get('file_token') for item in value]
        resp = await self.feishu.batch_get_tmp_download_url(file_tokens, extra)

        for item in resp.get('tmp_download_urls', []):
            res.append(item.get('tmp_download_url'))
        return res

    #构造条件筛选
    def build_condition(self, condition: dict[str, str]) -> str:
        condition_list = []
        for key, value in condition.items():
            condition_list.append(f"{key} = '{value}'")
        return " and ".join(condition_list)

    # 构造飞书多维表格筛选条件
    def build_filter_condition(self, field_name: str, operator: str, value: any = None) -> dict:
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
