
# main.py
"""主程序入口"""

from ollama_vision.chat_interface import start_chat

from ollama_vision.gui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())