import sys
import os
import loguru

# 从环境变量读取配置，设置默认值
log_config = {
    "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    "LOG_FILE": os.getenv("LOG_FILE", "logs/app.log"),
    "LOG_ROTATION": os.getenv("LOG_ROTATION", "500 MB"),
    "LOG_COMPRESSION": os.getenv("LOG_COMPRESSION", "zip")
}

# 配置日志
loguru.logger.configure(
    handlers=[
        {"sink": sys.stderr, "level": log_config["LOG_LEVEL"], "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{file}:{line}</cyan> | <yellow>{function}</yellow> | <white>{message}</white>"}
    ]
)

# 确保日志目录存在
os.makedirs(os.path.dirname(log_config["LOG_FILE"]), exist_ok=True)

loguru.logger.add(
    log_config["LOG_FILE"],
    rotation=log_config["LOG_ROTATION"],
    compression=log_config["LOG_COMPRESSION"],
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {function} | {message}"
)

# 删除重复的配置
logger = loguru.logger