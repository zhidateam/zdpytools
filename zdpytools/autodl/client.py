"""
AutoDL API异步客户端
"""
import os
import json
import httpx
import traceback
from typing import Dict, List, Union, Optional, Any

from ..utils.log import logger
from .const import *
from .exception import AutoDLException


class AutoDLClient:
    """
    AutoDL API异步客户端
    提供对AutoDL弹性部署API的异步访问
    """
    def __init__(self, token: str = os.getenv("AUTODL_TOKEN"), timeout: float = 30.0, print_log: bool = True):
        """
        初始化AutoDL API客户端
        
        Args:
            token: AutoDL API令牌，可从控制台 -> 设置 -> 开发者Token获取
            timeout: API请求超时时间（秒）
            print_log: 是否打印API请求日志
        """
        if not token:
            raise ValueError("AutoDL API令牌不能为空，请提供token参数或设置AUTODL_TOKEN环境变量")
        
        self._token = token
        self.print_log = print_log
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self) -> None:
        """
        关闭异步客户端
        """
        if self.client:
            await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _request(self, method: str, url: str, data: Dict = None, check_code: bool = True) -> Dict:
        """
        发送API请求
        
        Args:
            method: HTTP方法（GET, POST, PUT, DELETE）
            url: API URL
            data: 请求数据
            check_code: 是否检查响应代码
            
        Returns:
            API响应数据
        """
        headers = {
            "Authorization": self._token,
            "Content-Type": "application/json"
        }
        
        if self.print_log:
            logger.debug(f"{method} 请求AutoDL接口: {url}")
            if data:
                logger.debug(f"请求体: {data}")
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, headers=headers)
            else:
                response = await self.client.request(
                    method.upper(), 
                    url, 
                    headers=headers, 
                    json=data
                )
            
            response.raise_for_status()
            resp_data = response.json()
            
            if self.print_log:
                logger.debug(f"AutoDL接口响应: {resp_data}")
            
            if check_code and resp_data.get("code") != "Success":
                logger.error(f"接口返回错误, URL: {url}, 错误信息: {resp_data}")
                raise AutoDLException(
                    code=resp_data.get("code"), 
                    msg=resp_data.get("msg"), 
                    url=url, 
                    req_body=data, 
                    headers=headers
                )
            
            return resp_data
        except httpx.HTTPError as e:
            logger.error(f"请求AutoDL接口异常: {e}, URL: {url}")
            raise AutoDLException(
                code=-1, 
                msg=f"请求失败: {str(e)}", 
                url=url, 
                req_body=data, 
                headers=headers
            )
        except json.JSONDecodeError as e:
            logger.error(f"解析响应JSON失败: {e}, URL: {url}")
            raise AutoDLException(
                code=-1, 
                msg="响应解析失败", 
                url=url, 
                req_body=data, 
                headers=headers
            )
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"请求AutoDL接口未知异常: {e}, URL: {url}\n{tb}")
            raise AutoDLException(
                code=-1, 
                msg=f"未知错误: {str(e)}", 
                url=url, 
                req_body=data, 
                headers=headers
            )
    
    # 镜像相关API
    async def get_private_images(self, page_index: int = 1, page_size: int = 10, offset: int = 0) -> Dict:
        """
        获取私有镜像列表
        
        Args:
            page_index: 页码
            page_size: 每页条目数
            offset: 查询的起始偏移量
            
        Returns:
            私有镜像列表
        """
        url = f"{AUTODL_API_HOST}{IMAGE_PRIVATE_LIST_URI}"
        data = {
            "page_index": page_index,
            "page_size": page_size
        }
        
        if offset > 0:
            data["offset"] = offset
        
        response = await self._request("POST", url, data)
        return response.get("data", {})
    
    # 部署相关API
    async def create_deployment(self, 
                               name: str, 
                               deployment_type: str, 
                               container_template: Dict, 
                               replica_num: int = None, 
                               parallelism_num: int = None, 
                               reuse_container: bool = True,
                               service_port_protocol: str = "http") -> str:
        """
        创建部署
        
        Args:
            name: 部署名称
            deployment_type: 部署类型，支持ReplicaSet、Job、Container
            container_template: 容器模板配置
            replica_num: 创建容器的副本数量，ReplicaSet、Job必填
            parallelism_num: Job类型部署同时在运行的容器容量，Job必填
            reuse_container: 是否复用已经停止的容器
            service_port_protocol: 服务端口协议，可取值http/tcp，默认http
            
        Returns:
            部署UUID
        """
        url = f"{AUTODL_API_HOST}{DEPLOYMENT_CREATE_URI}"
        
        data = {
            "name": name,
            "deployment_type": deployment_type,
            "reuse_container": reuse_container,
            "container_template": container_template
        }
        
        if service_port_protocol and service_port_protocol.lower() in ["http", "tcp"]:
            data["service_port_protocol"] = service_port_protocol.lower()
        
        if deployment_type in ["ReplicaSet", "Job"]:
            if replica_num is None:
                raise ValueError(f"{deployment_type}类型部署必须提供replica_num参数")
            data["replica_num"] = replica_num
        
        if deployment_type == "Job":
            if parallelism_num is None:
                raise ValueError("Job类型部署必须提供parallelism_num参数")
            data["parallelism_num"] = parallelism_num
        
        response = await self._request("POST", url, data)
        return response.get("data", {}).get("deployment_uuid", "")
    
    async def get_deployments(self, 
                             page_index: int = 1, 
                             page_size: int = 10, 
                             name: str = None, 
                             status: str = None, 
                             deployment_uuid: str = None) -> Dict:
        """
        获取部署列表
        
        Args:
            page_index: 页码
            page_size: 每页条目数
            name: 根据name筛选，不支持模糊查询
            status: 根据部署的状态筛选，可选值：running, stopped
            deployment_uuid: 根据部署的UUID筛选
            
        Returns:
            部署列表
        """
        url = f"{AUTODL_API_HOST}{DEPLOYMENT_LIST_URI}"
        
        data = {
            "page_index": page_index,
            "page_size": page_size
        }
        
        if name:
            data["name"] = name
        
        if status:
            data["status"] = status
        
        if deployment_uuid:
            data["deployment_uuid"] = deployment_uuid
        
        response = await self._request("POST", url, data)
        return response.get("data", {})
    
    async def stop_deployment(self, deployment_uuid: str) -> bool:
        """
        停止部署
        
        Args:
            deployment_uuid: 部署UUID
            
        Returns:
            是否成功
        """
        url = f"{AUTODL_API_HOST}{DEPLOYMENT_OPERATE_URI}"
        
        data = {
            "deployment_uuid": deployment_uuid,
            "operate": "stop"
        }
        
        response = await self._request("PUT", url, data)
        return response.get("code") == "Success"
    
    async def delete_deployment(self, deployment_uuid: str) -> bool:
        """
        删除部署
        
        Args:
            deployment_uuid: 部署UUID
            
        Returns:
            是否成功
        """
        url = f"{AUTODL_API_HOST}{DEPLOYMENT_DELETE_URI}"
        
        data = {
            "deployment_uuid": deployment_uuid
        }
        
        response = await self._request("DELETE", url, data)
        return response.get("code") == "Success"
    
    async def set_replica_num(self, deployment_uuid: str, replica_num: int) -> bool:
        """
        设置副本数量
        
        Args:
            deployment_uuid: 部署UUID
            replica_num: 副本数量
            
        Returns:
            是否成功
        """
        url = f"{AUTODL_API_HOST}{DEPLOYMENT_REPLICA_NUM_URI}"
        
        data = {
            "deployment_uuid": deployment_uuid,
            "replica_num": replica_num
        }
        
        response = await self._request("PUT", url, data)
        return response.get("code") == "Success"
    
    # 容器相关API
    async def get_containers(self, 
                            deployment_uuid: str, 
                            container_uuid: str = None, 
                            status: List[str] = None, 
                            released: bool = False, 
                            page_index: int = 1, 
                            page_size: int = 10, 
                            **kwargs) -> Dict:
        """
        获取容器列表
        
        Args:
            deployment_uuid: 部署UUID
            container_uuid: 筛选container uuid
            status: 筛选指定状态的容器，可设置多个不同状态筛选
            released: 是否查询已经释放的实例
            page_index: 页码
            page_size: 每页条目数
            **kwargs: 其他筛选参数，如date_from, date_to, gpu_name等
            
        Returns:
            容器列表
        """
        url = f"{AUTODL_API_HOST}{CONTAINER_LIST_URI}"
        
        data = {
            "deployment_uuid": deployment_uuid,
            "page_index": page_index,
            "page_size": page_size,
            "released": released
        }
        
        if container_uuid:
            data["container_uuid"] = container_uuid
        
        if status:
            data["status"] = status
        
        # 添加其他可选筛选参数
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value
        
        response = await self._request("POST", url, data)
        return response.get("data", {})
    
    async def get_container_events(self, 
                                  deployment_uuid: str, 
                                  deployment_container_uuid: str = None, 
                                  page_index: int = 1, 
                                  page_size: int = 10, 
                                  offset: int = 0) -> Dict:
        """
        获取容器事件列表
        
        Args:
            deployment_uuid: 部署UUID
            deployment_container_uuid: 容器UUID
            page_index: 页码
            page_size: 每页条目数
            offset: 查询的起始偏移量
            
        Returns:
            容器事件列表
        """
        url = f"{AUTODL_API_HOST}{CONTAINER_EVENT_LIST_URI}"
        
        data = {
            "deployment_uuid": deployment_uuid,
            "page_index": page_index,
            "page_size": page_size
        }
        
        if deployment_container_uuid:
            data["deployment_container_uuid"] = deployment_container_uuid
        
        if offset > 0:
            data["offset"] = offset
        
        response = await self._request("POST", url, data)
        return response.get("data", {})
    
    async def stop_container(self, 
                            deployment_container_uuid: str, 
                            decrease_one_replica_num: bool = False, 
                            cmd_before_shutdown: str = None) -> bool:
        """
        停止容器
        
        Args:
            deployment_container_uuid: 容器UUID
            decrease_one_replica_num: 对于ReplicaSet类型的部署，是否同时将replica num副本数减少1个
            cmd_before_shutdown: 在停止容器前先执行的命令
            
        Returns:
            是否成功
        """
        url = f"{AUTODL_API_HOST}{CONTAINER_STOP_URI}"
        
        data = {
            "deployment_container_uuid": deployment_container_uuid,
            "decrease_one_replica_num": decrease_one_replica_num
        }
        
        if cmd_before_shutdown:
            data["cmd_before_shutdown"] = cmd_before_shutdown
        
        response = await self._request("PUT", url, data)
        return response.get("code") == "Success"
    
    # 黑名单相关API
    async def add_to_blacklist(self, 
                              deployment_container_uuid: str, 
                              expire_in_minutes: int = 1440, 
                              comment: str = None) -> bool:
        """
        将容器所在主机添加到调度黑名单
        
        Args:
            deployment_container_uuid: 容器UUID
            expire_in_minutes: 黑名单过期时间（分钟），默认24小时
            comment: 备注信息
            
        Returns:
            是否成功
        """
        url = f"{AUTODL_API_HOST}{BLACKLIST_CREATE_URI}"
        
        data = {
            "deployment_container_uuid": deployment_container_uuid,
            "expire_in_minutes": expire_in_minutes
        }
        
        if comment:
            data["comment"] = comment
        
        response = await self._request("POST", url, data)
        return response.get("code") == "Success"
    
    async def get_blacklist(self) -> List[Dict]:
        """
        获取生效中的调度黑名单
        
        Returns:
            黑名单列表
        """
        url = f"{AUTODL_API_HOST}{BLACKLIST_LIST_URI}"
        
        response = await self._request("GET", url)
        return response.get("data", [])
    
    # GPU库存相关API
    async def get_gpu_stock(self, 
                           region_sign: str, 
                           cuda_v_from: int = None, 
                           cuda_v_to: int = None, 
                           gpu_name_set: List[str] = None, 
                           **kwargs) -> List[Dict]:
        """
        获取GPU库存
        
        Args:
            region_sign: 地区代码，见const.py中的REGION_CODES
            cuda_v_from: CUDA版本范围下限
            cuda_v_to: CUDA版本范围上限
            gpu_name_set: GPU型号列表
            **kwargs: 其他筛选参数
            
        Returns:
            GPU库存列表
        """
        url = f"{AUTODL_API_HOST}{GPU_STOCK_URI}"
        
        data = {
            "region_sign": region_sign
        }
        
        if cuda_v_from:
            data["cuda_v_from"] = cuda_v_from
        
        if cuda_v_to:
            data["cuda_v_to"] = cuda_v_to
        
        if gpu_name_set:
            data["gpu_name_set"] = gpu_name_set
        
        # 添加其他可选筛选参数
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value
        
        response = await self._request("POST", url, data)
        return response.get("data", [])
