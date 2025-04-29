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

    logger.info("开始测试列出数据表API")

    try:
        # 多维表格信息
        app_token = "YOUR_APP_TOKEN"  # 替换为你的多维表格 app_token
        
        # 示例1: 基本用法，获取第一页数据表
        result1 = await fs.list_tables(
            app_token=app_token
        )
        logger.info(f"列出数据表结果: {result1}")
        
        # 示例2: 指定页面大小
        result2 = await fs.list_tables(
            app_token=app_token,
            page_size=5
        )
        logger.info(f"指定页面大小结果: {result2}")
        
        # 示例3: 使用分页标记获取下一页
        if result2.get("has_more") and result2.get("page_token"):
            result3 = await fs.list_tables(
                app_token=app_token,
                page_token=result2.get("page_token"),
                page_size=5
            )
            logger.info(f"获取下一页结果: {result3}")
        
        # 示例4: 获取所有数据表（自动处理分页）
        all_tables = await fs.get_all_tables(app_token=app_token)
        logger.info(f"获取所有数据表: 共 {len(all_tables)} 个表")
        for table in all_tables:
            logger.info(f"表格ID: {table.get('id')}, 名称: {table.get('name')}")

    except Exception as e:
        logger.error(f"发生错误: {e}")
    finally:
        await fs.close()
        logger.info("已关闭飞书客户端")

if __name__ == "__main__":
    asyncio.run(main())
