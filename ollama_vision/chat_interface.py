# chat_interface.py
"""交互式聊天界面模块"""


from ollama_vision.client import OllamaVisionClient
from ollama_vision.exceptions import OllamaClientError

def start_chat():
    """启动一个支持图片上传的交互式聊天界面"""
    client = OllamaVisionClient()
    print(f"已连接到Ollama服务,使用{client.model}模型")
    print("\n基础命令:")
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
        except OllamaClientError as e:
            print(f"\n发生错误: {str(e)}")
            current_images = []

    print("\n对话已结束")