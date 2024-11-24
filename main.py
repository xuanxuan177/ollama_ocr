import requests
import json
import base64
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Generator, List, Union


class OllamaVisionClient:
    """用于与本地ollama视觉模型服务进行交互的客户端类"""

    def __init__(
            self,
            base_url: str = "http://localhost:11434",
            model: str = "llama3.2-vision:latest",
            temperature: float = 0.7
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

    def _encode_image(self, image_path: Union[str, Path]) -> str:
        """
        将图片文件编码为base64字符串

        Args:
            image_path: 图片文件路径

        Returns:
            base64编码的图片字符串
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"找不到文件: {image_path}")

        # 检查文件类型
        mime_type = mimetypes.guess_type(image_path)[0]
        if not mime_type or not mime_type.startswith('image/'):
            raise ValueError(f"不支持的文件类型: {mime_type}")

        # 检查文件大小
        file_size = image_path.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise ValueError("文件太大,请使用小于10MB的图片")

        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            raise IOError(f"读取图片失败: {str(e)}")

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
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise ConnectionError(f"请求失败: {str(e)}")

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
        data = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": stream
        }

        # 处理图片
        if image_paths:
            images = []
            for path in image_paths:
                try:
                    image_data = self._encode_image(path)
                    images.append({
                        "data": image_data,
                        "mime_type": mimetypes.guess_type(path)[0]
                    })
                except Exception as e:
                    raise ValueError(f"处理图片 {path} 失败: {str(e)}")

            if images:
                data["images"] = images

        if system_prompt:
            data["system"] = system_prompt

        response = self._make_request("api/generate", data, stream=stream)

        if stream:
            for line in response.iter_lines():
                if line:
                    try:
                        response_data = json.loads(line)
                        if "response" in response_data:
                            yield response_data["response"]
                    except json.JSONDecodeError:
                        continue
        else:
            response_data = response.json()
            if "response" in response_data:
                yield response_data["response"]


def start_chat():
    """启动一个支持图片上传的交互式聊天界面"""
    client = OllamaVisionClient()
    print(f"已连接到Ollama服务,使用{client.model}模型")
    print("基础命令:")
    print("- 输入 'quit' 或 'exit' 退出对话")
    print("- 输入 '/upload 图片路径' 上传图片")
    print("- 多个图片路径用空格分隔")

    current_images = []

    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            break

        if user_input.startswith('/upload '):
            # 处理图片上传
            paths = user_input[8:].split()
            current_images = paths
            print(f"已添加图片: {', '.join(paths)}")
            continue

        print("\n助手: ", end="", flush=True)
        try:
            for text in client.chat(user_input, image_paths=current_images):
                print(text, end="", flush=True)
            # 每次对话后清空图片列表
            current_images = []
        except Exception as e:
            print(f"\n发生错误: {str(e)}")
            current_images = []

    print("\n对话已结束")


if __name__ == "__main__":
    start_chat()