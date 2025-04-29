import asyncio
import os
from zdpytools.feishu import Feishu
from zdpytools.utils.log import logger

# 设置环境变量（也可以在系统中设置）
os.environ["FEISHU_APP_ID"] = "你的飞书应用ID"
os.environ["FEISHU_APP_SECRET"] = "你的飞书应用密钥"

async def main():
    # 直接传入应用ID和密钥
    # fs = Feishu(app_id="你的飞书应用ID", app_secret="你的飞书应用密钥")

    # 或使用环境变量
    fs = Feishu()

    logger.info("开始测试复制多维表格API")

    try:
        # 要复制的多维表格信息
        app_token = "YOUR_APP_TOKEN"  # 替换为要复制的多维表格 app_token
        
        # 示例1: 简单复制，使用原表格名称
        result1 = await fs.copy_bitable(
            app_token=app_token
        )
        logger.info(f"简单复制结果: {result1}")
        logger.info(f"新表格的 app_token: {result1.get('app_token')}")
        
        # 示例2: 复制并指定新名称
        result2 = await fs.copy_bitable(
            app_token=app_token,
            name="复制的多维表格 - " + app_token
        )
        logger.info(f"指定名称复制结果: {result2}")
        
        # 示例3: 复制到指定文件夹，不复制内容
        folder_token = "YOUR_FOLDER_TOKEN"  # 替换为目标文件夹的 token
        result3 = await fs.copy_bitable(
            app_token=app_token,
            name="仅结构 - " + app_token,
            folder_token=folder_token,
            without_content=True
        )
        logger.info(f"复制到指定文件夹结果: {result3}")
        
    except Exception as e:
        logger.error(f"发生错误: {e}")
    finally:
        await fs.close()
        logger.info("已关闭飞书客户端")

if __name__ == "__main__":
    asyncio.run(main())
