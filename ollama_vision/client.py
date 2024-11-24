# ollama_vision/client.py
"""Ollama视觉模型客户端模块"""

import requests
import json
import mimetypes
from typing import Optional, Dict, Generator, List, Union
from pathlib import Path

from ollama_vision.config import DEFAULT_BASE_URL, DEFAULT_MODEL, DEFAULT_TEMPERATURE, CHAT_ENDPOINT
from ollama_vision.exceptions import APIError, ConfigurationError
from ollama_vision.image_utils import encode_image


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

    def _make_request(
            self,
            endpoint: str,
            data: Dict,
            stream: bool = True
    ) -> requests.Response:
        """发送POST请求到指定的endpoint"""
        url = f"{self.base_url}/{endpoint}"
        try:
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
            raise APIError(f"请求失败: {str(e)}")

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