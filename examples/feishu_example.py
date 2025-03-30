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

    logger.info("开始调用飞书API")

    try:
        # 查询多维表格记录
        app_token = "YOUR_APP_TOKEN"
        table_id = "YOUR_TABLE_ID"

        result = await fs.bitable_records_search(
            app_token=app_token,
            table_id=table_id,
            req_body={"filter": {"conjunction": "AND", "conditions": []}}
        )

        logger.info(f"查询结果: {result}")

        # 更新记录示例
        # new_record = await fs.update_bitable_record(
        #     app_token=app_token,
        #     table_id=table_id,
        #     fields={"字段名": "值"}
        # )
        # logger.info(f"新增记录: {new_record}")

    except Exception as e:
        logger.error(f"发生错误: {e}")
    finally:
        await fs.close()
        logger.info("已关闭飞书客户端")

if __name__ == "__main__":
    asyncio.run(main())