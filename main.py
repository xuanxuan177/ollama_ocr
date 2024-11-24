import requests
import json
from typing import Optional, Dict, Generator


class OllamaClient:
    """用于与本地ollama服务进行交互的客户端类"""

    def __init__(
            self,
            base_url: str = "http://localhost:11434",
            model: str = "llama3.2-vision:latest",
            temperature: float = 0.7
    ):
        """
        初始化Ollama客户端

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
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise ConnectionError(f"请求失败: {str(e)}")

    def chat(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            stream: bool = True
    ) -> Generator[str, None, None]:
        """
        与模型进行对话

        Args:
            prompt: 用户输入的提示词
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
    """启动一个简单的交互式聊天界面"""
    client = OllamaClient()
    print(f"已连接到Ollama服务,使用{client.model}模型")
    print("输入 'quit' 或 'exit' 退出对话")

    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            break

        print("\n助手: ", end="", flush=True)
        try:
            for text in client.chat(user_input):
                print(text, end="", flush=True)
        except Exception as e:
            print(f"\n发生错误: {str(e)}")

    print("\n对话已结束")


if __name__ == "__main__":
    start_chat()