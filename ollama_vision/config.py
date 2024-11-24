"""配置参数模块"""

# API设置
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2-vision:latest"
DEFAULT_TEMPERATURE = 0.7

# 图片设置
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
SUPPORTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']

# API端点
CHAT_ENDPOINT = "api/chat"