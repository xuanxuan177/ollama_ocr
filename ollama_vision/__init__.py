# ollama_vision/__init__.py
"""
Ollama Vision Client
A Python client for interacting with Ollama vision models
"""

__version__ = "0.1.0"

from ollama_vision.client import OllamaVisionClient
from ollama_vision.chat_interface import start_chat

__all__ = ['OllamaVisionClient', 'start_chat']