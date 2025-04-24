import asyncio
from zdpytools.utils.download import download_file, download_file_async

async def main():
    # 测试同步下载
    print("测试同步下载...")
    try:
        filename, content = download_file("https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png")
        print(f"同步下载成功: {filename}, 大小: {len(content)} 字节")
    except Exception as e:
        print(f"同步下载失败: {e}")

    # 测试异步下载
    print("\n测试异步下载...")
    try:
        filename, content = await download_file_async("https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png")
        print(f"异步下载成功: {filename}, 大小: {len(content)} 字节")
    except Exception as e:
        print(f"异步下载失败: {e}")

    # 测试重定向下载
    print("\n测试重定向下载...")
    try:
        # 使用一个会重定向的URL
        filename, content = await download_file_async("https://httpbin.org/redirect/2")  # 这个URL会重定向两次
        print(f"重定向下载成功: {filename}, 大小: {len(content)} 字节")
    except Exception as e:
        print(f"重定向下载失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
