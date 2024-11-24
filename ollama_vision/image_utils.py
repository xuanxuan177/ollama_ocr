# image_utils.py
"""图片处理工具模块"""

import base64
import mimetypes
from pathlib import Path
from typing import Union

from ollama_vision.config import MAX_IMAGE_SIZE, SUPPORTED_IMAGE_TYPES
from ollama_vision.exceptions import ImageProcessingError

def encode_image(image_path: Union[str, Path]) -> str:
    """
    将图片文件编码为base64字符串

    Args:
        image_path: 图片文件路径

    Returns:
        base64编码的图片字符串

    Raises:
        ImageProcessingError: 当图片处理失败时
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise ImageProcessingError(f"找不到文件: {image_path}")

    # 检查文件类型
    mime_type = mimetypes.guess_type(image_path)[0]
    if not mime_type or mime_type not in SUPPORTED_IMAGE_TYPES:
        raise ImageProcessingError(f"不支持的文件类型: {mime_type}")

    # 检查文件大小
    file_size = image_path.stat().st_size
    if file_size > MAX_IMAGE_SIZE:
        raise ImageProcessingError(f"文件太大,请使用小于{MAX_IMAGE_SIZE / 1024 / 1024}MB的图片")

    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        raise ImageProcessingError(f"读取图片失败: {str(e)}")