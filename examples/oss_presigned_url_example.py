#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OSS预签名URL示例

演示如何使用zdpytools.utils.Oss生成预签名URL，用于临时访问私有Bucket中的文件
"""

import asyncio
import os
import json
from zdpytools.utils.Oss import Oss
from zdpytools.utils.log import logger


async def main():
    # 从环境变量或配置文件中获取OSS配置
    # 可以根据实际情况修改配置获取方式
    oss_config = {
        "access_key": os.environ.get("OSS_ACCESS_KEY", ""),
        "access_secret": os.environ.get("OSS_ACCESS_SECRET", ""),
        "region": os.environ.get("OSS_REGION", "oss-cn-hangzhou"),
        "bucket": os.environ.get("OSS_BUCKET", ""),
        "root_path": os.environ.get("OSS_ROOT_PATH", "")
    }
    
    # 初始化OSS客户端
    oss = Oss(oss_config)
    
    # 示例1: 同步生成预签名URL
    file_path = "example/test.txt"
    url = oss.get_presigned_url(file_path, expires=3600)  # 1小时有效期
    if url:
        logger.info(f"同步生成的预签名URL: {url}")
        logger.info(f"此URL有效期为1小时，可以直接在浏览器中访问或使用HTTP客户端下载文件")
    else:
        logger.error("生成预签名URL失败")
    
    # 示例2: 异步生成预签名URL
    file_path = "example/image.jpg"
    url = await oss.get_presigned_url_async(file_path, expires=7200)  # 2小时有效期
    if url:
        logger.info(f"异步生成的预签名URL: {url}")
        logger.info(f"此URL有效期为2小时，可以直接在浏览器中访问或使用HTTP客户端下载文件")
    else:
        logger.error("异步生成预签名URL失败")
    
    # 示例3: 生成PUT方法的预签名URL，用于上传文件
    file_path = "example/upload.txt"
    url = oss.get_presigned_url(file_path, expires=1800, http_method='PUT')  # 30分钟有效期
    if url:
        logger.info(f"用于上传的预签名URL: {url}")
        logger.info(f"可以使用此URL通过PUT请求上传文件，例如：")
        logger.info(f"curl -X PUT -T local_file.txt '{url}'")
    else:
        logger.error("生成上传用预签名URL失败")


if __name__ == "__main__":
    asyncio.run(main())
