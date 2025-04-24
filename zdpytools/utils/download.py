import os
import tempfile
import urllib.parse
import httpx
import asyncio
import mimetypes
from typing import Optional, Tuple, Union, BinaryIO, Dict
from pathlib import Path
from .log import logger
import traceback


def get_extension_from_mime_type(mime_type: str) -> str:
    """
    根据MIME类型获取文件扩展名

    Args:
        mime_type: MIME类型，如'image/jpeg'

    Returns:
        str: 文件扩展名（包含点，如'.jpg'），如果无法确定则返回空字符串
    """
    if not mime_type:
        return ""

    # 初始化mimetypes模块
    mimetypes.init()

    # 获取扩展名
    ext = mimetypes.guess_extension(mime_type)

    # 一些常见MIME类型的特殊处理
    mime_to_ext = {
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp',
        'image/svg+xml': '.svg',
        'application/pdf': '.pdf',
        'application/json': '.json',
        'text/html': '.html',
        'text/plain': '.txt',
        'text/csv': '.csv',
        'application/zip': '.zip',
        'application/x-zip-compressed': '.zip',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
        'application/msword': '.doc',
        'application/vnd.ms-excel': '.xls',
        'application/vnd.ms-powerpoint': '.ppt',
        'audio/mpeg': '.mp3',
        'audio/mp4': '.m4a',
        'video/mp4': '.mp4',
        'video/mpeg': '.mpeg',
        'video/quicktime': '.mov',
        'video/x-msvideo': '.avi',
        'video/webm': '.webm',
    }

    # 如果在自定义映射中找到，使用自定义映射
    if mime_type.lower() in mime_to_ext:
        return mime_to_ext[mime_type.lower()]

    # 否则使用mimetypes模块的结果
    return ext if ext else ""


def extract_filename_from_response(response, url: str) -> Tuple[str, str]:
    """
    从响应头或URL中提取文件名和MIME类型

    Args:
        response: HTTP响应对象
        url: 请求的URL

    Returns:
        Tuple[str, str]: 包含(文件名, MIME类型)的元组，如果无法提取则返回默认名称和空MIME类型
    """
    # 获取MIME类型
    mime_type = response.headers.get('content-type', '').split(';')[0].strip()

    # 先尝试从Content-Disposition获取文件名
    content_disposition = response.headers.get('content-disposition')
    if content_disposition and 'filename=' in content_disposition:
        filename = content_disposition.split('filename=')[-1].strip('"\'')
    else:
        # 如果没有Content-Disposition，从URL路径获取文件名
        filename = os.path.basename(urllib.parse.urlparse(url).path)
        if not filename:
            filename = 'downloaded_file'

    # 如果文件名没有扩展名，但有MIME类型，尝试添加扩展名
    if '.' not in filename and mime_type:
        ext = get_extension_from_mime_type(mime_type)
        if ext:
            filename = f"{filename}{ext}"

    return filename, mime_type


def download_file(url: str, output_path: Optional[str] = None, follow_redirects: bool = True) -> Tuple[str, bytes]:
    """
    从URL下载文件，支持302重定向追踪

    Args:
        url: 需要下载的文件URL
        output_path: 保存文件的路径，如果不提供则只返回文件内容不保存
        follow_redirects: 是否跟踪重定向，默认为True

    Returns:
        Tuple[str, bytes]: 包含(文件名, 文件内容)的元组

    Example:
        >>> filename, content = download_file('https://example.com/file.jpg')
        >>> print(f"Downloaded {filename}, size: {len(content)} bytes")
        'Downloaded file.jpg, size: 12345 bytes'

        >>> filename, _ = download_file('https://example.com/file.jpg', '/path/to/save/file.jpg')
        >>> print(f"Saved as {filename}")
        'Saved as file.jpg'
    """
    try:
        # 添加User-Agent头以避免某些网站的403错误
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        with httpx.Client(follow_redirects=follow_redirects) as client:
            with client.stream('GET', url, headers=headers) as response:
                response.raise_for_status()

                # 获取文件名和MIME类型
                filename, mime_type = extract_filename_from_response(response, url)
                logger.debug(f"从 {url} 下载文件 {filename}，MIME类型: {mime_type}")

                # 如果提供了输出路径但没有指定文件名，使用提取的文件名
                if output_path:
                    if os.path.isdir(output_path):
                        output_path = os.path.join(output_path, filename)
                else:
                    # 如果没有提供输出路径，创建临时文件
                    output_path = None

                # 读取文件内容
                content = b''
                for chunk in response.iter_bytes(chunk_size=8192):
                    if chunk:
                        content += chunk

                # 如果需要保存文件
                if output_path:
                    # 确保目录存在
                    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

                    # 写入文件
                    with open(output_path, 'wb') as f:
                        f.write(content)

                return filename, content

    except Exception as e:
        errmsg = f"{e}\n{traceback.format_exc()}"
        logger.error(f"下载文件失败: {errmsg}")
        raise


def download_file_to_temp(url: str, follow_redirects: bool = True) -> Tuple[str, str]:
    """
    从URL下载文件到临时文件

    Args:
        url: 需要下载的文件URL
        follow_redirects: 是否跟踪重定向，默认为True

    Returns:
        Tuple[str, str]: 包含(文件名, 临时文件路径)的元组

    Example:
        >>> filename, temp_path = download_file_to_temp('https://example.com/file.jpg')
        >>> print(f"Downloaded {filename} to {temp_path}")
        'Downloaded file.jpg to /tmp/tmpxyz123.jpg'
    """
    try:
        # 添加User-Agent头以避免某些网站的403错误
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            with httpx.Client(follow_redirects=follow_redirects) as client:
                with client.stream('GET', url, headers=headers) as response:
                    response.raise_for_status()

                    # 获取文件名和MIME类型
                    filename, mime_type = extract_filename_from_response(response, url)
                    logger.debug(f"从 {url} 下载文件 {filename}，MIME类型: {mime_type}")

                    # 流式下载文件
                    for chunk in response.iter_bytes(chunk_size=8192):
                        if chunk:
                            tmp_file.write(chunk)

                    # 确保数据写入磁盘
                    tmp_file.flush()
                    os.fsync(tmp_file.fileno())
                    # 关闭文件句柄
                    tmp_file.close()

                    return filename, tmp_file.name
        except Exception:
            # 确保文件句柄已关闭
            if not tmp_file.closed:
                tmp_file.close()
            # 删除临时文件
            try:
                os.unlink(tmp_file.name)
            except Exception as e:
                logger.warning(f"删除临时文件失败: {e}")
            raise
    except Exception as e:
        errmsg = f"{e}\n{traceback.format_exc()}"
        logger.error(f"下载文件到临时文件失败: {errmsg}")
        raise


async def download_file_async(url: str, output_path: Optional[str] = None, follow_redirects: bool = True) -> Tuple[str, bytes]:
    """
    异步从URL下载文件，支持302重定向追踪

    Args:
        url: 需要下载的文件URL
        output_path: 保存文件的路径，如果不提供则只返回文件内容不保存
        follow_redirects: 是否跟踪重定向，默认为True

    Returns:
        Tuple[str, bytes]: 包含(文件名, 文件内容)的元组

    Example:
        >>> filename, content = await download_file_async('https://example.com/file.jpg')
        >>> print(f"Downloaded {filename}, size: {len(content)} bytes")
        'Downloaded file.jpg, size: 12345 bytes'

        >>> filename, _ = await download_file_async('https://example.com/file.jpg', '/path/to/save/file.jpg')
        >>> print(f"Saved as {filename}")
        'Saved as file.jpg'
    """
    try:
        # 添加User-Agent头以避免某些网站的403错误
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        async with httpx.AsyncClient(follow_redirects=follow_redirects) as client:
            async with client.stream('GET', url, headers=headers) as response:
                response.raise_for_status()

                # 获取文件名和MIME类型
                filename, mime_type = extract_filename_from_response(response, url)
                logger.debug(f"从 {url} 下载文件 {filename}，MIME类型: {mime_type}")

                # 如果提供了输出路径但没有指定文件名，使用提取的文件名
                if output_path:
                    if os.path.isdir(output_path):
                        output_path = os.path.join(output_path, filename)
                else:
                    # 如果没有提供输出路径，创建临时文件
                    output_path = None

                # 读取文件内容
                content = b''
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    if chunk:
                        content += chunk

                # 如果需要保存文件
                if output_path:
                    # 确保目录存在
                    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

                    # 写入文件
                    with open(output_path, 'wb') as f:
                        f.write(content)

                return filename, content

    except Exception as e:
        errmsg = f"{e}\n{traceback.format_exc()}"
        logger.error(f"异步下载文件失败: {errmsg}")
        raise


async def download_file_to_temp_async(url: str, follow_redirects: bool = True) -> Tuple[str, str]:
    """
    异步从URL下载文件到临时文件

    Args:
        url: 需要下载的文件URL
        follow_redirects: 是否跟踪重定向，默认为True

    Returns:
        Tuple[str, str]: 包含(文件名, 临时文件路径)的元组

    Example:
        >>> filename, temp_path = await download_file_to_temp_async('https://example.com/file.jpg')
        >>> print(f"Downloaded {filename} to {temp_path}")
        'Downloaded file.jpg to /tmp/tmpxyz123.jpg'
    """
    try:
        # 添加User-Agent头以避免某些网站的403错误
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            async with httpx.AsyncClient(follow_redirects=follow_redirects) as client:
                async with client.stream('GET', url, headers=headers) as response:
                    response.raise_for_status()

                    # 获取文件名和MIME类型
                    filename, mime_type = extract_filename_from_response(response, url)
                    logger.debug(f"从 {url} 下载文件 {filename}，MIME类型: {mime_type}")

                    # 流式下载文件
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        if chunk:
                            tmp_file.write(chunk)

                    # 确保数据写入磁盘
                    tmp_file.flush()
                    os.fsync(tmp_file.fileno())
                    # 关闭文件句柄
                    tmp_file.close()

                    return filename, tmp_file.name
        except Exception:
            # 确保文件句柄已关闭
            if not tmp_file.closed:
                tmp_file.close()
            # 删除临时文件
            try:
                os.unlink(tmp_file.name)
            except Exception as e:
                logger.warning(f"删除临时文件失败: {e}")
            raise
    except Exception as e:
        errmsg = f"{e}\n{traceback.format_exc()}"
        logger.error(f"异步下载文件到临时文件失败: {errmsg}")
        raise
