# ollama_vision/gui/main_window.py

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSplitter, QListWidget, QComboBox,
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from ollama_vision.client import OllamaVisionClient
from ollama_vision.exceptions import APIError
from .chat_widget import ChatWidget


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.client = OllamaVisionClient()
        self.setWindowTitle("Ollama Vision")
        self.setMinimumSize(QSize(900, 600))

        self.init_ui()
        self.load_models()

    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # 左侧边栏
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setMaximumWidth(250)
        sidebar.setMinimumWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(8)

        # 模型选择区域
        model_layout = QVBoxLayout()
        model_layout.setSpacing(4)

        model_label = QLabel("选择模型")
        model_label.setFont(QFont("苹方", 11))
        model_label.setStyleSheet("color: #666666;")
        model_layout.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.setFont(QFont("苹方", 11))
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(self.model_combo)

        sidebar_layout.addLayout(model_layout)

        # 分割线
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #E0E0E0;")
        sidebar_layout.addWidget(line)

        # 新建对话按钮
        new_chat_btn = QPushButton("新建对话")
        new_chat_btn.setObjectName("new-chat-btn")
        new_chat_btn.setFont(QFont("苹方", 12))
        new_chat_btn.setMinimumHeight(36)
        new_chat_btn.clicked.connect(self.new_chat)
        sidebar_layout.addWidget(new_chat_btn)

        # 对话历史列表
        self.chat_list = QListWidget()
        self.chat_list.setFont(QFont("苹方", 11))
        sidebar_layout.addWidget(self.chat_list)

        # 添加到分割器
        splitter.addWidget(sidebar)

        # 主聊天区域
        self.chat_widget = ChatWidget(self.client)
        splitter.addWidget(self.chat_widget)

        # 设置分割比例
        splitter.setStretchFactor(0, 1)  # 侧边栏
        splitter.setStretchFactor(1, 4)  # 聊天区域

        self.load_stylesheet()

    def load_stylesheet(self):
        """加载QSS样式表"""
        try:
            with open("ollama_vision/gui/style.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"加载样式表失败: {e}")

    def load_models(self):
        """加载可用的模型列表"""
        try:
            models = self.client.get_models()
            if not models:
                QMessageBox.warning(
                    self,
                    "警告",
                    "没有找到支持vision功能的模型!\n请先使用ollama pull命令下载支持vision的模型。"
                )
                return

            self.model_combo.clear()
            self.model_combo.addItems(models)

            # 设置当前选中的模型
            current_index = self.model_combo.findText(self.client.model)
            if current_index >= 0:
                self.model_combo.setCurrentIndex(current_index)

        except APIError as e:
            QMessageBox.critical(
                self,
                "错误",
                f"加载模型列表失败: {str(e)}\n请确保ollama服务已启动。"
            )

    def on_model_changed(self, model_name):
        """模型选择改变时的处理"""
        self.client.set_model(model_name)
        # 可以在这里添加提示或其他处理

    def new_chat(self):
        """创建新对话"""
        self.chat_widget.clear()