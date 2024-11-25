# ollama_vision/gui/chat_thread.py

from PyQt6.QtCore import QThread, pyqtSignal
import time
from ollama_vision.exceptions import OllamaClientError


class UploadThread(QThread):
    """图片上传处理线程"""

    progress = pyqtSignal(int)  # 上传进度
    finished = pyqtSignal(str)  # 上传完成,返回base64
    error = pyqtSignal(str)  # 上传错误

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        """执行上传任务"""
        try:
            # 模拟上传进度
            for i in range(0, 101, 10):
                self.progress.emit(i)
                time.sleep(0.1)  # 模拟网络延迟

            from ollama_vision.image_utils import encode_image
            # 实际进行base64编码
            encoded = encode_image(self.image_path)
            self.progress.emit(100)
            self.finished.emit(encoded)

        except Exception as e:
            self.error.emit(str(e))


class ChatThread(QThread):
    """聊天消息处理线程"""

    # 定义信号
    response_received = pyqtSignal(str)  # 收到回复
    error_occurred = pyqtSignal(str)  # 发生错误
    finished = pyqtSignal()  # 处理完成

    def __init__(self, client, prompt, encoded_images=None):
        super().__init__()
        self.client = client
        self.prompt = prompt
        self.encoded_images = encoded_images or []

    def run(self):
        """线程执行的任务"""
        try:
            # 构建消息
            messages = [{
                "role": "user",
                "content": self.prompt
            }]

            if self.encoded_images:
                messages[0]["images"] = self.encoded_images

            # 发送请求
            data = {
                "model": self.client.model,
                "messages": messages,
                "stream": True,
                "temperature": self.client.temperature
            }

            # 使用client发送请求
            response = self.client._make_request(
                "api/chat",
                data=data,
                stream=True
            )

            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    try:
                        import json
                        response_data = json.loads(line)
                        if "message" in response_data:
                            message = response_data["message"]
                            if message["role"] == "assistant" and "content" in message:
                                self.response_received.emit(message["content"])
                    except json.JSONDecodeError:
                        continue

        except OllamaClientError as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(f"发生未知错误: {str(e)}")
        finally:
            self.finished.emit()