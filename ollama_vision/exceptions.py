# exceptions.py
"""自定义异常类模块"""

class OllamaClientError(Exception):
    """基础异常类"""
    pass

class ImageProcessingError(OllamaClientError):
    """图片处理相关错误"""
    pass

class APIError(OllamaClientError):
    """API调用相关错误"""
    pass

class ConfigurationError(OllamaClientError):
    """配置相关错误"""
    pass