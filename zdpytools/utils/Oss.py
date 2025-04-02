import oss2
import urllib.parse
import json
from .log import logger
import traceback
from pathlib import Path
import asyncio


class Oss:
    def __init__(self, config: str|dict = ""):
        # 默认配置
        default_config = {
            "access_key": "",
            "access_secret": "",
            "region": "",
            "bucket": "",
            "root_path": ""
        }

        try:
            if isinstance(config, str):
                user_config = json.loads(config)
            else:
                user_config = config
            if "access_key" in user_config and "access_secret" in user_config \
                    and "region" in user_config and "bucket" in user_config:
                default_config.update(user_config)
            else:
                print(f"Invalid config: `{config}`.Maybe missing some keys like `access_key`, `access_secret`, `region`, `bucket`")

        except json.JSONDecodeError:
            pass  # 保留默认配置

        self.access_key = default_config["access_key"]
        self.access_secret = default_config["access_secret"]
        self.region = default_config["region"]
        self.bucket_name = default_config["bucket"]

        if "host" in default_config:
            self.endpoint = f"{self.region}.aliyuncs.com"
            host = default_config["host"]
            self.url = f"https://{host}"
        else:
            self.endpoint = f"{self.region}.aliyuncs.com"
            self.url = f"https://{self.bucket_name}.{self.endpoint}"
        self.auth = oss2.Auth(self.access_key, self.access_secret)
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
        self.root_path = default_config.get("root_path", "")

    def upload_file(self, local_file_path, oss_file_path):
        """
        上传文件到OSS
        :param local_file_path: 本地文件路径
        :param oss_file_path: OSS文件路径
        :return: OSS文件的URL路径
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            self.bucket.put_object_from_file(oss_file_path, local_file_path)
            path = f"{self.url}/{urllib.parse.quote(oss_file_path)}"
            return path
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"上传文件到OSS失败: {errmsg}")
            return ""

    async def upload_file_async(self, local_file_path, oss_file_path):
        """
        异步上传文件到OSS
        :param local_file_path: 本地文件路径
        :param oss_file_path: OSS文件路径
        :return: OSS文件的URL路径
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            await asyncio.to_thread(self.bucket.put_object_from_file, oss_file_path, local_file_path)
            path = f"{self.url}/{urllib.parse.quote(oss_file_path)}"
            return path
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"异步上传文件到OSS失败: {errmsg}")
            return ""

    def download_file(self, oss_file_path, local_file_path):
        """
        从OSS下载文件
        :param oss_file_path: OSS文件路径
        :param local_file_path: 本地保存路径
        :return: None
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            self.bucket.get_object_to_file(oss_file_path, local_file_path)
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"从OSS下载文件失败: {errmsg}")

    async def download_file_async(self, oss_file_path, local_file_path):
        """
        异步从OSS下载文件
        :param oss_file_path: OSS文件路径
        :param local_file_path: 本地保存路径
        :return: None
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            await asyncio.to_thread(self.bucket.get_object_to_file, oss_file_path, local_file_path)
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"异步从OSS下载文件失败: {errmsg}")

    def get_dir_size(self, path):
        """
        计算oss目录及其子目录的总大小，并转换为MB
        :param path: OSS目录路径
        :return: 目录总大小（MB）
        """
        try:
            path = self.get_remote_path(path)
            total_size = 0
            for obj in oss2.ObjectIteratorV2(self.bucket, prefix=path):
                total_size += obj.size

            total_size_mb = total_size / (1024 * 1024)
            return total_size_mb
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"计算OSS目录大小失败: {errmsg}")
            return 0

    async def get_dir_size_async(self, path):
        """
        异步计算oss目录及其子目录的总大小，并转换为MB
        :param path: OSS目录路径
        :return: 目录总大小（MB）
        """
        try:
            path = self.get_remote_path(path)
            total_size = 0
            for obj in oss2.ObjectIteratorV2(self.bucket, prefix=path):
                total_size += obj.size

            total_size_mb = total_size / (1024 * 1024)
            return total_size_mb
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"异步计算OSS目录大小失败: {errmsg}")
            return 0

    def list_files(self, prefix=''):
        """
        列出OSS指定前缀的文件
        :param prefix: 文件前缀
        :return: 文件列表
        """
        try:
            prefix = self.get_remote_path(prefix)
            files = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
                files.append(obj.key)
            return files
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"列出OSS文件失败: {errmsg}")
            return []

    async def list_files_async(self, prefix=''):
        """
        异步列出OSS指定前缀的文件
        :param prefix: 文件前缀
        :return: 文件列表
        """
        try:
            prefix = self.get_remote_path(prefix)
            files = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
                files.append(obj.key)
            return files
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"异步列出OSS文件失败: {errmsg}")
            return []

    def delete_file(self, oss_file_path):
        """
        删除OSS上的文件
        :param oss_file_path: OSS文件路径
        :return: None
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            self.bucket.delete_object(oss_file_path)
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"删除OSS文件失败: {errmsg}")

    async def delete_file_async(self, oss_file_path):
        """
        异步删除OSS上的文件
        :param oss_file_path: OSS文件路径
        :return: None
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            await asyncio.to_thread(self.bucket.delete_object, oss_file_path)
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"异步删除OSS文件失败: {errmsg}")

    def get_remote_path(self, oss_file_path):
        """
        根据root_path获取OSS文件路径
        :param oss_file_path: OSS文件路径
        :return: 完整的OSS文件路径
        """
        if self.root_path:
            if self.root_path.endswith("/"):
                self.root_path = self.root_path[:-1]
            oss_file_path = f"{self.root_path}/{oss_file_path}"
        if oss_file_path.startswith("/"):
            oss_file_path = oss_file_path[1:]
        if oss_file_path.endswith("//"):
            oss_file_path = oss_file_path[:-1]
        return oss_file_path
