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

    logger.info("开始测试飞书上传API")

    try:
        # 应用和表格信息
        app_token = "YOUR_APP_TOKEN"  # 替换为你的多维表格 app_token
        table_id = "YOUR_TABLE_ID"    # 替换为你的表格 ID
        
        # 示例1: 上传本地文件
        file_path = "path/to/your/file.jpg"  # 替换为实际文件路径
        result1 = await fs.upload_media(
            file_path=file_path,
            parent_type="docx_image",  # 上传为新版文档图片
            parent_node=app_token,
            extra={"bitablePerm": {"tableId": table_id, "rev": 5}}
        )
        logger.info(f"上传本地文件结果: {result1}")
        
        # 示例2: 更新记录，自动处理附件字段
        # 假设有一个名为"附件"的字段，类型为附件(17)
        fields = {
            "标题": "测试附件上传",
            "附件": file_path  # 可以是文件路径、URL或二进制内容
        }
        
        record = await fs.add_record(app_token, table_id, fields)
        logger.info(f"添加记录结果: {record}")
        
        # 示例3: 使用URL作为附件
        image_url = "https://example.com/image.jpg"  # 替换为实际URL
        fields = {
            "标题": "测试URL附件上传",
            "附件": image_url
        }
        
        record = await fs.add_record(app_token, table_id, fields)
        logger.info(f"添加URL附件记录结果: {record}")

    except Exception as e:
        logger.error(f"发生错误: {e}")
    finally:
        await fs.close()
        logger.info("已关闭飞书客户端")

if __name__ == "__main__":
    asyncio.run(main())
