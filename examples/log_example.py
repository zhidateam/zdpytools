import os
from zdpytools.utils.log import logger

# 可以通过环境变量修改日志配置
os.environ["LOG_LEVEL"] = "DEBUG"  # 修改日志级别
# os.environ["LOG_FILE"] = "custom_logs/app.log"  # 自定义日志文件路径

def main():
    # 输出不同级别的日志
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.critical("这是一条严重错误日志")

    # 带结构化数据的日志
    user_data = {"user_id": 12345, "username": "test_user", "role": "admin"}
    logger.info(f"用户登录: {user_data}")

    # 异常日志
    try:
        result = 10 / 0
    except Exception as e:
        logger.exception(f"发生异常: {e}")

    logger.info("程序执行完毕")

if __name__ == "__main__":
    main()