# ollama_vision/client.py

import requests
import json
import logging
from typing import Optional, Dict, Generator, List, Union, Any
from pathlib import Path
from dataclasses import dataclass

from ollama_vision.config import DEFAULT_BASE_URL, DEFAULT_MODEL, DEFAULT_TEMPERATURE, CHAT_ENDPOINT
from ollama_vision.exceptions import APIError, ConfigurationError
from ollama_vision.image_utils import encode_image

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """模型信息数据类"""
    name: str
    description: str = ""
    format: str = ""
    family: str = ""
    tag: str = "latest"
    size: int = 0
    capabilities: Dict[str, Any] = None
    parameters: Dict[str, Any] = None

    VISION_CAPABLE_FAMILIES = {
        'llama', 'llava', 'bakllava', 'mixtral', 'yi', 'qwen'  # 支持视觉的模型系列
    }

    VISION_CAPABILITY_INDICATORS = {
        'vision', 'multimodal', 'image', 'visual', 'img', 'images'  # 可能表示视觉能力的关键字
    }

    @property
    def display_name(self) -> str:
        """返回用于显示的模型名称"""
        base_name = self.name.split(":")[0]
        family = f"[{self.family}]" if self.family else ""
        size = f"{self.size / 1024 / 1024 / 1024:.1f}GB" if self.size else ""
        return f"{base_name} {family} {size}".strip()

    @property
    def supports_vision(self) -> bool:
        """检查是否支持视觉功能,使用更宽松的检测逻辑"""
        try:
            # 1. 检查模型家族
            model_family = self.family.lower()
            name_lower = self.name.lower()
            for family in self.VISION_CAPABLE_FAMILIES:
                if family in model_family or family in name_lower:
                    logger.debug(f"Model {self.name} supports vision based on family/name match with {family}")
                    return True

            # 2. 检查capabilities
            if self.capabilities:
                for indicator in self.VISION_CAPABILITY_INDICATORS:
                    if indicator in self.capabilities:
                        value = self.capabilities[indicator]
                        if isinstance(value, bool) and value:
                            logger.debug(f"Model {self.name} supports vision based on capability {indicator}")
                            return True
                        elif isinstance(value, (str, dict)):
                            logger.debug(f"Model {self.name} supports vision based on capability {indicator} presence")
                            return True

            # 3. 检查parameters
            if self.parameters:
                for indicator in self.VISION_CAPABILITY_INDICATORS:
                    if indicator in self.parameters:
                        value = self.parameters[indicator]
                        if isinstance(value, bool) and value:
                            logger.debug(f"Model {self.name} supports vision based on parameter {indicator}")
                            return True
                        elif isinstance(value, (str, dict)):
                            logger.debug(f"Model {self.name} supports vision based on parameter {indicator} presence")
                            return True

            # 4. 检查描述
            desc_lower = self.description.lower()
            for indicator in self.VISION_CAPABILITY_INDICATORS:
                if indicator in desc_lower:
                    logger.debug(f"Model {self.name} supports vision based on description containing {indicator}")
                    return True

            logger.debug(f"Model {self.name} does not appear to support vision")
            return False

        except Exception as e:
            logger.error(f"Error checking vision support for model {self.name}: {e}")
            return False


class OllamaVisionClient:
    """用于与本地ollama视觉模型服务进行交互的客户端类"""

    def __init__(
            self,
            base_url: str = DEFAULT_BASE_URL,
            model: str = DEFAULT_MODEL,
            temperature: float = DEFAULT_TEMPERATURE
    ):
        """
        初始化Ollama视觉模型客户端

        Args:
            base_url: Ollama服务的基础URL
            model: 要使用的模型名称
            temperature: 生成温度参数(0-1之间)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self._models_cache: List[ModelInfo] = []
        self._last_error: Optional[str] = None

    @property
    def last_error(self) -> Optional[str]:
        """返回最后一次错误信息"""
        return self._last_error

    def _make_request(
            self,
            endpoint: str,
            data: Optional[Dict] = None,
            method: str = "POST",
            stream: bool = True
    ) -> requests.Response:
        """发送HTTP请求到指定的endpoint"""
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url)
            else:
                response = requests.post(url, json=data, stream=stream)

            if not response.ok:
                error_msg = response.text
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error']
                except:
                    pass
                raise APIError(f"API错误 ({response.status_code}): {error_msg}")
            return response
        except requests.RequestException as e:
            self._last_error = str(e)
            raise APIError(f"请求失败: {str(e)}")

    def get_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """
        获取当前安装的模型列表

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            支持vision功能的模型信息列表
        """
        if not force_refresh and self._models_cache:
            return self._models_cache

        try:
            # 获取所有模型列表
            response = self._make_request("api/tags", method="GET")
            data = response.json()

            logger.debug(f"Found {len(data.get('models', []))} total models")

            models = []
            for model_data in data.get('models', []):
                name = model_data.get('name', '')

                # 获取模型详细信息
                model_info = self._make_request(
                    "api/show",
                    data={"name": name},
                    method="POST",
                    stream=False
                ).json()

                logger.debug(f"Model details for {name}: {json.dumps(model_info, indent=2)}")

                # 创建模型信息对象
                model = ModelInfo(
                    name=name,
                    description=model_info.get("description", ""),
                    format=model_info.get("format", ""),
                    family=model_info.get("families", [""])[0],
                    size=model_info.get("size", 0),
                    capabilities=model_info.get("capabilities", {}),
                    parameters=model_info.get("parameters", {})
                )

                # 使用改进后的视觉能力检测
                if model.supports_vision:
                    models.append(model)
                    logger.info(f"Added vision-capable model: {model.name}")
                else:
                    logger.debug(f"Skipped non-vision model: {model.name}")

            # 按照family和name排序
            models.sort(key=lambda m: (m.family or "zzzz", m.name))
            self._models_cache = models

            logger.info(f"Found {len(models)} vision-capable models")
            return models

        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Error getting models: {e}")
            raise APIError(f"获取模型列表失败: {str(e)}")

    def set_model(self, model_name: str):
        """
        切换使用的模型

        Args:
            model_name: 模型名称
        """
        self.model = model_name

    def chat(
            self,
            prompt: str,
            image_paths: Optional[List[Union[str, Path]]] = None,
            system_prompt: Optional[str] = None,
            stream: bool = True
    ) -> Generator[str, None, None]:
        """
        与模型进行对话

        Args:
            prompt: 用户输入的提示词
            image_paths: 图片文件路径列表(可选)
            system_prompt: 系统提示词(可选)
            stream: 是否使用流式输出

        Returns:
            生成器,用于获取模型的输出
        """
        messages = []

        # 添加系统提示
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # 处理用户消息
        user_message = {
            "role": "user",
            "content": prompt
        }

        # 处理图片
        if image_paths:
            images = []
            for path in image_paths:
                try:
                    image_data = encode_image(path)
                    images.append(image_data)
                except Exception as e:
                    raise APIError(f"处理图片 {path} 失败: {str(e)}")
            if images:
                user_message["images"] = images

        messages.append(user_message)

        # 构建请求数据
        data = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": self.temperature
        }

        # 发送请求
        response = self._make_request(CHAT_ENDPOINT, data, stream=stream)

        if stream:
            for line in response.iter_lines():
                if line:
                    try:
                        response_data = json.loads(line)
                        if "message" in response_data:
                            message = response_data["message"]
                            if message["role"] == "assistant" and "content" in message:
                                yield message["content"]
                    except json.JSONDecodeError:
                        continue
        else:
            response_data = response.json()
            if "message" in response_data:
                message = response_data["message"]
                if message["role"] == "assistant" and "content" in message:
                    yield message["content"]