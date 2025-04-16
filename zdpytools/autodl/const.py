"""
AutoDL API常量定义
"""

# API基础URL
AUTODL_API_HOST = "https://api.autodl.com"

# API路径
# 镜像相关
IMAGE_PRIVATE_LIST_URI = "/api/v1/dev/image/private/list"

# 部署相关
DEPLOYMENT_CREATE_URI = "/api/v1/dev/deployment"
DEPLOYMENT_LIST_URI = "/api/v1/dev/deployment/list"
DEPLOYMENT_OPERATE_URI = "/api/v1/dev/deployment/operate"
DEPLOYMENT_DELETE_URI = "/api/v1/dev/deployment"
DEPLOYMENT_REPLICA_NUM_URI = "/api/v1/dev/deployment/replica_num"

# 容器相关
CONTAINER_LIST_URI = "/api/v1/dev/deployment/container/list"
CONTAINER_EVENT_LIST_URI = "/api/v1/dev/deployment/container/event/list"
CONTAINER_STOP_URI = "/api/v1/dev/deployment/container/stop"

# 黑名单相关
BLACKLIST_CREATE_URI = "/api/v1/dev/deployment/blacklist"
BLACKLIST_LIST_URI = "/api/v1/dev/deployment/blacklist"

# GPU库存相关
GPU_STOCK_URI = "/api/v1/dev/machine/region/gpu_stock"

# 地区代码
REGION_CODES = {
    "西北企业区": "westDC2",
    "西北B区": "westDC3",
    "北京A区": "beijingDC1",
    "北京B区": "beijingDC2",
    "L20专区": "beijingDC4",
    "V100专区": "beijingDC3",
    "内蒙A区": "neimengDC1",
    "佛山区": "foshanDC1",
    "重庆A区": "chongqingDC1",
    "3090专区": "yangzhouDC1",
    "内蒙B区": "neimengDC3"
}

# 基础镜像UUID
BASE_IMAGES = {
    "PyTorch 1.9.0": "base-image-12be412037",
    "PyTorch 1.10.0": "base-image-u9r24vthlk",
    "PyTorch 1.11.0": "base-image-l374uiucui",
    "PyTorch 2.0.0": "base-image-l2t43iu6uk",
    "TensorFlow 2.5.0": "base-image-0gxqmciyth",
    "TensorFlow 2.9.0": "base-image-uxeklgirir",
    "TensorFlow 1.15.5": "base-image-4bpg0tt88l",
    "Miniconda (CUDA 11.6)": "base-image-mbr2n4urrc",
    "Miniconda (CUDA 10.2)": "base-image-qkkhitpik5",
    "Miniconda (CUDA 11.1)": "base-image-h041hn36yt",
    "Miniconda (CUDAGL 11.3)": "base-image-7bn8iqhkb5",
    "Miniconda (CUDA 9.0)": "base-image-k0vep6kyq8",
    "TensorRT 8.5.1": "base-image-l2843iu23k",
    "TensorRT (PyTorch 2.0.0)": "base-image-l2t43iu6uk"
}

# 部署类型
DEPLOYMENT_TYPES = {
    "ReplicaSet": "ReplicaSet",
    "Job": "Job",
    "Container": "Container"
}

# 容器状态
CONTAINER_STATUS = {
    "creating": "创建中",
    "created": "已创建",
    "starting": "启动中",
    "running": "运行中",
    "shutting_down": "关闭中",
    "shutdown": "已关闭",
    "oss_merged": "OSS已合并"
}
