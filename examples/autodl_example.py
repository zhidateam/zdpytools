"""
AutoDL API使用示例
"""
import os
import asyncio
from zdpytools.autodl import AutoDLClient
from zdpytools.utils.log import logger

# 设置环境变量（也可以直接在代码中传入token）
# os.environ["AUTODL_TOKEN"] = "your_token_here"

async def list_images_example():
    """获取私有镜像列表示例"""
    async with AutoDLClient() as client:
        try:
            images = await client.get_private_images(page_size=5)
            logger.info(f"获取到 {len(images.get('list', []))} 个私有镜像")
            for image in images.get("list", []):
                logger.info(f"镜像名称: {image.get('name')}, UUID: {image.get('image_uuid')}")
        except Exception as e:
            logger.error(f"获取镜像列表失败: {e}")

async def list_deployments_example():
    """获取部署列表示例"""
    async with AutoDLClient() as client:
        try:
            deployments = await client.get_deployments(page_size=5)
            logger.info(f"获取到 {len(deployments.get('list', []))} 个部署")
            for deployment in deployments.get("list", []):
                logger.info(f"部署名称: {deployment.get('name')}, UUID: {deployment.get('uuid')}, 状态: {deployment.get('status')}")
        except Exception as e:
            logger.error(f"获取部署列表失败: {e}")

async def create_deployment_example():
    """创建部署示例"""
    async with AutoDLClient() as client:
        try:
            # 创建ReplicaSet类型部署
            container_template = {
                "dc_list": ["westDC2", "westDC3"],
                "gpu_name_set": ["RTX 4090"],
                "gpu_num": 1,
                "cuda_v_from": 113,
                "cuda_v_to": 128,
                "cpu_num_from": 1,
                "cpu_num_to": 100,
                "memory_size_from": 1,
                "memory_size_to": 256,
                "cmd": "sleep 100",
                "price_from": 100,  # 基准价格：0.1元/小时
                "price_to": 9000,   # 基准价格：9元/小时
                "image_uuid": "base-image-l2t43iu6uk"  # PyTorch 2.0.0
            }
            
            deployment_uuid = await client.create_deployment(
                name="API测试部署",
                deployment_type="ReplicaSet",
                replica_num=1,
                container_template=container_template
            )
            
            logger.info(f"创建部署成功，UUID: {deployment_uuid}")
            return deployment_uuid
        except Exception as e:
            logger.error(f"创建部署失败: {e}")
            return None

async def get_containers_example(deployment_uuid):
    """获取容器列表示例"""
    if not deployment_uuid:
        logger.error("部署UUID为空，无法获取容器列表")
        return
    
    async with AutoDLClient() as client:
        try:
            # 等待容器创建和启动
            logger.info("等待容器创建和启动...")
            await asyncio.sleep(10)
            
            containers = await client.get_containers(deployment_uuid=deployment_uuid)
            logger.info(f"获取到 {len(containers.get('list', []))} 个容器")
            
            for container in containers.get("list", []):
                logger.info(f"容器UUID: {container.get('uuid')}, 状态: {container.get('status')}")
                
                # 如果容器正在运行，显示SSH连接信息
                if container.get("status") == "running":
                    info = container.get("info", {})
                    logger.info(f"SSH命令: {info.get('ssh_command')}")
                    logger.info(f"SSH密码: {info.get('root_password')}")
                    logger.info(f"服务URL: {info.get('service_url')}")
            
            return containers.get("list", [])
        except Exception as e:
            logger.error(f"获取容器列表失败: {e}")
            return []

async def stop_deployment_example(deployment_uuid):
    """停止部署示例"""
    if not deployment_uuid:
        logger.error("部署UUID为空，无法停止部署")
        return False
    
    async with AutoDLClient() as client:
        try:
            success = await client.stop_deployment(deployment_uuid=deployment_uuid)
            if success:
                logger.info(f"停止部署成功，UUID: {deployment_uuid}")
            else:
                logger.error(f"停止部署失败，UUID: {deployment_uuid}")
            return success
        except Exception as e:
            logger.error(f"停止部署失败: {e}")
            return False

async def get_gpu_stock_example():
    """获取GPU库存示例"""
    async with AutoDLClient() as client:
        try:
            # 获取西北企业区的GPU库存
            gpu_stock = await client.get_gpu_stock(
                region_sign="westDC2",
                cuda_v_from=117,
                cuda_v_to=128
            )
            
            logger.info(f"获取到 {len(gpu_stock)} 种GPU的库存信息")
            for gpu_info in gpu_stock:
                for gpu_name, stock in gpu_info.items():
                    logger.info(f"GPU型号: {gpu_name}, 空闲数量: {stock.get('idle_gpu_num')}, 总数量: {stock.get('total_gpu_num')}")
        except Exception as e:
            logger.error(f"获取GPU库存失败: {e}")

async def main():
    """主函数"""
    logger.info("开始AutoDL API示例")
    
    # 获取私有镜像列表
    await list_images_example()
    
    # 获取部署列表
    await list_deployments_example()
    
    # 获取GPU库存
    await get_gpu_stock_example()
    
    # 创建部署（取消注释以测试创建部署）
    # deployment_uuid = await create_deployment_example()
    # if deployment_uuid:
    #     # 获取容器列表
    #     containers = await get_containers_example(deployment_uuid)
    #     
    #     # 停止部署
    #     await stop_deployment_example(deployment_uuid)

if __name__ == "__main__":
    # 设置token（也可以通过环境变量设置）
    # os.environ["AUTODL_TOKEN"] = "your_token_here"
    
    asyncio.run(main())
