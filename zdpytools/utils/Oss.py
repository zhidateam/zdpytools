import datetime
import random
import time
import oss2
import urllib.parse
import json
from .log import logger
import traceback
from pathlib import Path
import asyncio
from typing import Any, Dict, Optional, Union, List
import os
from .download import download_file_to_temp, download_file_to_temp_async


class Oss:
    def __init__(self, config: Union[str, Dict[str, Any]] = "") -> None:
        """
        初始化OSS客户端

        Args:
            config: OSS配置信息，可以是JSON字符串或字典，包含以下字段：
                - access_key: 阿里云OSS的AccessKey ID
                - access_secret: 阿里云OSS的AccessKey Secret
                - region: OSS的区域，如'oss-cn-hangzhou'
                - bucket: OSS的存储桶名称
                - root_path: 可选，OSS中的根路径前缀
                - host: 可选，自定义域名

        Returns:
            None
        """
        # 默认配置
        default_config = {
            "access_key": "",
            "access_secret": "",
            "region": "",
            "bucket": "",
            "root_path": "",
            "host": ""
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

        host_name = default_config["host"]

        if host_name:
            self.endpoint = f"{self.region}.aliyuncs.com"
            # host = default_config["host"]
            self.url = f"https://{host_name}"
        else:
            self.endpoint = f"{self.region}.aliyuncs.com"
            self.url = f"https://{self.bucket_name}.{self.endpoint}"
        self.auth = oss2.Auth(self.access_key, self.access_secret)
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
        self.root_path = default_config.get("root_path", "")

    def upload_file_from_url(self, url: str, oss_file_path: Optional[str] = "",headers=None,
                             progress_callback=None) -> str:
        """
        从URL下载文件并上传到OSS，使用流式传输以节省内存

        Args:
            url: 需要下载的文件URL
            oss_file_path: OSS中的目标路径，如'images/file.jpg' 或 'images/file'。
                          如果不提供，将从URL或响应头中获取文件名

        Returns:
            str: 上传成功返回OSS文件的完整URL路径，失败返回空字符串

        Example:
            >>> oss = Oss(config)
            >>> url = oss.upload_file_from_url('https://example.com/file.jpg')
            >>> print(url)
            'https://bucket-name.oss-cn-hangzhou.aliyuncs.com/images/file.jpg'
        """
        try:
            # 使用新的下载函数，支持302重定向追踪
            filename, tmp_file_path = download_file_to_temp(url, follow_redirects=True)

            try:
                # 如果没有提供oss_file_path，使用下载时获取的文件名
                if not oss_file_path:
                    oss_file_path = filename

                # 上传文件到OSS
                result = self.upload_file(tmp_file_path, oss_file_path)
                return result
            finally:
                # 删除临时文件
                try:
                    os.unlink(tmp_file_path)
                except Exception as e:
                    logger.warning(f"删除临时文件失败: {e}")

        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"从URL上传文件到OSS失败: {errmsg}")
            return ""

    async def upload_file_from_url_async(self, url: str, oss_file_path: Optional[str] = None,headers=None,
                             progress_callback=None) -> str:
        """
        异步从URL下载文件并上传到OSS，使用流式传输以节省内存

        Args:
            url: 需要下载的文件URL
            oss_file_path: OSS中的目标路径，如'images/file.jpg'。
                          如果不提供，将从URL或响应头中获取文件名

        Returns:
            str: 上传成功返回OSS文件的完整URL路径，失败返回空字符串

        Example:
            >>> oss = Oss(config)
            >>> url = await oss.upload_file_from_url_async('https://example.com/file.jpg')
            >>> print(url)
            'https://bucket-name.oss-cn-hangzhou.aliyuncs.com/images/file.jpg'
        """
        try:
            # 使用新的异步下载函数，支持302重定向追踪
            filename, tmp_file_path = await download_file_to_temp_async(url, follow_redirects=True)

            try:
                # 如果没有提供oss_file_path，使用下载时获取的文件名
                if not oss_file_path:
                    oss_file_path = filename

                # 上传文件到OSS
                result = await self.upload_file_async(tmp_file_path, oss_file_path)
                return result
            finally:
                # 删除临时文件
                try:
                    os.unlink(tmp_file_path)
                except Exception as e:
                    logger.warning(f"删除临时文件失败: {e}")

        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"异步从URL上传文件到OSS失败: {errmsg}")
            return ""

    def upload_file(self, local_file_path: str, oss_file_path: str,headers=None,
                             progress_callback=None) -> str:
        """
        上传文件到OSS

        Args:
            local_file_path: 本地文件的完整路径，如'/path/to/file.jpg'
            oss_file_path: OSS中的目标路径，如'images/file.jpg'

        Returns:
            str: 上传成功返回OSS文件的完整URL路径，失败返回空字符串

        Example:
            >>> oss = Oss(config)
            >>> url = oss.upload_file('/path/to/file.jpg', 'images/file.jpg')
            >>> print(url)
            'https://bucket-name.oss-cn-hangzhou.aliyuncs.com/images/file.jpg'
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            self.bucket.put_object_from_file(oss_file_path, local_file_path,
                                             headers=None,
                             progress_callback=None)
            path = f"{self.url}/{urllib.parse.quote(oss_file_path)}"
            return path
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"上传文件到OSS失败: {errmsg}")
            return ""

    async def upload_file_async(self, local_file_path: str, oss_file_path: str,headers=None,
                             progress_callback=None) -> str:
        """
        异步上传文件到OSS

        Args:
            local_file_path: 本地文件的完整路径，如'/path/to/file.jpg'
            oss_file_path: OSS中的目标路径，如'images/file.jpg'

        Returns:
            str: 上传成功返回OSS文件的完整URL路径，失败返回空字符串

        Example:
            >>> oss = Oss(config)
            >>> url = await oss.upload_file_async('/path/to/file.jpg', 'images/file.jpg')
            >>> print(url)
            'https://bucket-name.oss-cn-hangzhou.aliyuncs.com/images/file.jpg'
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

    def download_file(self, oss_file_path: str, local_file_path: str) -> None:
        """
        从OSS下载文件

        Args:
            oss_file_path: OSS中的文件路径，如'images/file.jpg'
            local_file_path: 本地保存的完整路径，如'/path/to/save/file.jpg'

        Returns:
            None: 该方法没有返回值，下载失败会记录错误日志

        Example:
            >>> oss = Oss(config)
            >>> oss.download_file('images/file.jpg', '/path/to/save/file.jpg')
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            self.bucket.get_object_to_file(oss_file_path, local_file_path)
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"从OSS下载文件失败: {errmsg}")

    async def download_file_async(self, oss_file_path: str, local_file_path: str) -> None:
        """
        异步从OSS下载文件
        :param oss_file_path: OSS中的文件路径，如'images/file.jpg'
        :type oss_file_path: str
        :param local_file_path: 本地保存的完整路径，如'/path/to/save/file.jpg'
        :type local_file_path: str
        :return: 无返回值，下载失败会记录错误日志
        :rtype: None

        示例::
            oss = Oss(config)
            await oss.download_file_async('images/file.jpg', '/path/to/save/file.jpg')
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            await asyncio.to_thread(self.bucket.get_object_to_file, oss_file_path, local_file_path)
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"异步从OSS下载文件失败: {errmsg}")

    def get_dir_size(self, path: str) -> float:
        """
        计算OSS目录及其子目录的总大小，并转换为MB

        Args:
            path: OSS中的目录路径，如'images/'

        Returns:
            float: 目录总大小，单位为MB，计算失败返回0

        Example:
            >>> oss = Oss(config)
            >>> size_mb = oss.get_dir_size('images/')
            >>> print(f"目录大小: {size_mb:.2f} MB")
            '目录大小: 15.25 MB'
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

    async def get_dir_size_async(self, path: str) -> float:
        """
        异步计算OSS目录及其子目录的总大小，并转换为MB

        Args:
            path: OSS中的目录路径，如'images/'

        Returns:
            float: 目录总大小，单位为MB，计算失败返回0

        Example:
            >>> oss = Oss(config)
            >>> size_mb = await oss.get_dir_size_async('images/')
            >>> print(f"目录大小: {size_mb:.2f} MB")
            '目录大小: 15.25 MB'
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

    def list_files(self, prefix: str = '') -> List[str]:
        """
        列出OSS指定前缀的文件

        Args:
            prefix: OSS中的文件前缀，如'images/'，默认为空字符串（列出所有文件）

        Returns:
            list: 文件路径列表，失败返回空列表

        Example:
            >>> oss = Oss(config)
            >>> files = oss.list_files('images/')
            >>> print(files)
            ['images/file1.jpg', 'images/file2.png', 'images/subfolder/file3.jpg']
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

    async def list_files_async(self, prefix: str = '') -> List[str]:
        """
        异步列出OSS指定前缀的文件

        Args:
            prefix: OSS中的文件前缀，如'images/'，默认为空字符串（列出所有文件）

        Returns:
            list: 文件路径列表，失败返回空列表

        Example:
            >>> oss = Oss(config)
            >>> files = await oss.list_files_async('images/')
            >>> print(files)
            ['images/file1.jpg', 'images/file2.png', 'images/subfolder/file3.jpg']
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

    def delete_file(self, oss_file_path: str) -> None:
        """
        删除OSS上的文件

        Args:
            oss_file_path: OSS中的文件路径，如'images/file.jpg'

        Returns:
            None: 该方法没有返回值，删除失败会记录错误日志

        Example:
            >>> oss = Oss(config)
            >>> oss.delete_file('images/file.jpg')
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            self.bucket.delete_object(oss_file_path)
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"删除OSS文件失败: {errmsg}")

    async def delete_file_async(self, oss_file_path: str) -> None:
        """
        异步删除OSS上的文件

        Args:
            oss_file_path: OSS中的文件路径，如'images/file.jpg'

        Returns:
            None: 该方法没有返回值，删除失败会记录错误日志

        Example:
            >>> oss = Oss(config)
            >>> await oss.delete_file_async('images/file.jpg')
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            await asyncio.to_thread(self.bucket.delete_object, oss_file_path)
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"异步删除OSS文件失败: {errmsg}")

    def get_remote_path(self, oss_file_path: str) -> str:
        """
        根据root_path获取OSS文件完整路径，处理路径格式

        Args:
            oss_file_path: OSS中的相对文件路径，如'images/file.jpg'

        Returns:
            str: 处理后的完整OSS文件路径，包含root_path前缀（如果有）

        Note:
            此方法会处理以下情况：
            1. 添加root_path前缀（如果配置了）
            2. 移除开头的斜杠
            3. 修复结尾的双斜杠

        Example:
            >>> oss = Oss({"root_path": "my-project"})
            >>> path = oss.get_remote_path('images/file.jpg')
            >>> print(path)
            'my-project/images/file.jpg'
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

    def get_presigned_url(self, oss_file_path: str, expires: int = 3600, http_method: str = 'GET', slash_safe: bool = True) -> str:
        """
        生成OSS文件的预签名URL，用于临时访问私有Bucket中的文件

        Args:
            oss_file_path: OSS中的文件路径，如'images/file.jpg'
            expires: URL的有效期，单位为秒，默认为3600秒（1小时），最长为7天
            http_method: HTTP请求方法，默认为'GET'
            slash_safe: 是否对URL中的斜杠进行安全处理，默认为True

        Returns:
            str: 预签名URL，失败返回空字符串

        Example:
            >>> oss = Oss(config)
            >>> url = oss.get_presigned_url('images/file.jpg', 3600)
            >>> print(url)
            'https://bucket-name.oss-cn-hangzhou.aliyuncs.com/images/file.jpg?OSSAccessKeyId=xxx&Expires=xxx&Signature=xxx'
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            url = self.bucket.sign_url(http_method, oss_file_path, expires, slash_safe=slash_safe)
            return url
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"生成预签名URL失败: {errmsg}")
            return ""

    async def get_presigned_url_async(self, oss_file_path: str, expires: int = 3600, http_method: str = 'GET', slash_safe: bool = True) -> str:
        """
        异步生成OSS文件的预签名URL，用于临时访问私有Bucket中的文件

        Args:
            oss_file_path: OSS中的文件路径，如'images/file.jpg'
            expires: URL的有效期，单位为秒，默认为3600秒（1小时），最长为7天
            http_method: HTTP请求方法，默认为'GET'
            slash_safe: 是否对URL中的斜杠进行安全处理，默认为True

        Returns:
            str: 预签名URL，失败返回空字符串

        Example:
            >>> oss = Oss(config)
            >>> url = await oss.get_presigned_url_async('images/file.jpg', 3600)
            >>> print(url)
            'https://bucket-name.oss-cn-hangzhou.aliyuncs.com/images/file.jpg?OSSAccessKeyId=xxx&Expires=xxx&Signature=xxx'
        """
        try:
            oss_file_path = self.get_remote_path(oss_file_path)
            # 使用asyncio.to_thread将同步操作转换为异步操作
            url = await asyncio.to_thread(self.bucket.sign_url, http_method, oss_file_path, expires, slash_safe=slash_safe)
            return url
        except Exception as e:
            errmsg = f"{e}\n{traceback.format_exc()}"
            logger.error(f"异步生成预签名URL失败: {errmsg}")
            return ""
