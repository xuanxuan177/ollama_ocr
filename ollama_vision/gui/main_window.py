# ollama_vision/gui/main_window.py

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSplitter, QListWidget, QComboBox,
    QLabel, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QSize, QEasingCurve, QPropertyAnimation, QPoint
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor

from ollama_vision.client import OllamaVisionClient, ModelInfo
from ollama_vision.exceptions import APIError
from .chat_widget import ChatWidget


class NotionComboBox(QComboBox):
    """Notion风格的下拉框组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                background-color: #fbfbfa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                color: #11181c;
                min-width: 180px;
            }
            QComboBox:hover {
                border-color: #c0c0c0;
                background-color: #f7f7f7;
            }
            QComboBox:focus {
                border-color: #3b82f6;
                outline: none;
            }
            QComboBox::drop-down {
                width: 20px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: url(resources/icons/chevron-down.svg);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                selection-background-color: #f0f0f0;
                selection-color: #11181c;
                padding: 4px;
            }
        """)


class NotionButton(QPushButton):
    """Notion风格的按钮组件"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #fbfbfa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                color: #11181c;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #f7f7f7;
                border-color: #c0c0c0;
            }
            QPushButton:pressed {
                background-color: #f0f0f0;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #a0a0a0;
                border-color: #e0e0e0;
            }
        """)


class NotionListWidget(QListWidget):
    """Notion风格的列表组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QListWidget {
                background-color: #fbfbfa;
                border: none;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                background-color: transparent;
                border-radius: 6px;
                padding: 8px;
                margin: 2px 4px;
            }
            QListWidget::item:hover {
                background-color: #f7f7f7;
            }
            QListWidget::item:selected {
                background-color: #f0f0f0;
                color: #11181c;
            }
        """)


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.client = OllamaVisionClient()
        self.setWindowTitle("Ollama Vision")
        self.setMinimumSize(QSize(1000, 700))

        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #fbfbfa;
            }
            QSplitter::handle {
                background-color: #e0e0e0;
                margin: 0px 4px;
            }
            QScrollBar:vertical {
                background-color: #fbfbfa;
        # ollama_vision/gui/main_window.py (continued)
                        width: 8px;
                        border: none;
                        border-radius: 4px;
                    }
                    QScrollBar::handle:vertical {
                        background-color: #e0e0e0;
                        min-height: 30px;
                        border-radius: 4px;
                    }
                    QScrollBar::handle:vertical:hover {
                        background-color: #c0c0c0;
                    }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                    QScrollBar:horizontal {
                        background-color: #fbfbfa;
                        height: 8px;
                        border: none;
                        border-radius: 4px;
                    }
                    QScrollBar::handle:horizontal {
                        background-color: #e0e0e0;
                        min-width: 30px;
                        border-radius: 4px;
                    }
                    QScrollBar::handle:horizontal:hover {
                        background-color: #c0c0c0;
                    }
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                        width: 0px;
                    }
                    QLabel {
                        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        color: #11181c;
                    }
                """)

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
        splitter.setHandleWidth(1)  # 设置分割线宽度
        layout.addWidget(splitter)

        # 左侧边栏
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setMaximumWidth(280)
        sidebar.setMinimumWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(16)

        # 添加图标和标题
        header_layout = QHBoxLayout()
        title_label = QLabel("Ollama Vision")
        title_label.setStyleSheet("""
                    QLabel {
                        font-size: 18px;
                        font-weight: bold;
                        color: #11181c;
                    }
                """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        sidebar_layout.addLayout(header_layout)

        # 模型选择区域
        model_section = QFrame()
        model_section.setStyleSheet("""
                    QFrame {
                        background-color: #ffffff;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        padding: 12px;
                    }
                """)
        model_layout = QVBoxLayout(model_section)
        model_layout.setSpacing(8)

        model_header = QLabel("模型选择")
        model_header.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        font-weight: 500;
                        color: #6b7280;
                        margin-bottom: 4px;
                    }
                """)
        model_layout.addWidget(model_header)

        self.model_combo = NotionComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(self.model_combo)

        # 添加刷新按钮
        refresh_btn = NotionButton("刷新模型列表")
        refresh_btn.clicked.connect(lambda: self.load_models(force_refresh=True))
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        model_layout.addWidget(refresh_btn)

        sidebar_layout.addWidget(model_section)

        # 新建对话按钮
        new_chat_btn = NotionButton("新建对话")
        new_chat_btn.setObjectName("new-chat-btn")
        new_chat_btn.setIcon(QIcon.fromTheme("document-new"))
        new_chat_btn.clicked.connect(self.new_chat)
        new_chat_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3b82f6;
                        color: white;
                        border: none;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #2563eb;
                    }
                    QPushButton:pressed {
                        background-color: #1d4ed8;
                    }
                """)
        sidebar_layout.addWidget(new_chat_btn)

        # 对话历史列表
        history_label = QLabel("历史对话")
        history_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        font-weight: 500;
                        color: #6b7280;
                        margin: 8px 0;
                    }
                """)
        sidebar_layout.addWidget(history_label)

        self.chat_list = NotionListWidget()
        sidebar_layout.addWidget(self.chat_list)

        # 添加到分割器
        splitter.addWidget(sidebar)

        # 主聊天区域
        chat_container = QFrame()
        chat_container.setStyleSheet("""
                    QFrame {
                        background-color: #ffffff;
                        border-left: 1px solid #e0e0e0;
                    }
                """)
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        self.chat_widget = ChatWidget(self.client)
        chat_layout.addWidget(self.chat_widget)

        splitter.addWidget(chat_container)

        # 设置分割比例
        splitter.setStretchFactor(0, 0)  # 侧边栏不伸缩
        splitter.setStretchFactor(1, 1)  # 聊天区域自适应

    def load_models(self, force_refresh: bool = False):
        """加载可用的模型列表"""
        try:
            # 显示加载状态
            self.model_combo.setEnabled(False)
            self.model_combo.clear()
            self.model_combo.addItem("正在加载模型列表...")

            # 获取模型列表
            models = self.client.get_models(force_refresh=force_refresh)

            if not models:
                QMessageBox.warning(
                    self,
                    "提示",
                    "未检测到支持视觉功能的模型。\n\n"
                    "可能的原因：\n"
                    "1. 模型信息获取不完整，请尝试重启Ollama服务\n"
                    "2. 当前安装的模型不支持视觉功能\n"
                    "3. 模型能力检测失败\n\n"
                    "请确保您的模型支持视觉功能。\n"
                    "如有疑问，请查看Ollama服务日志获取详细信息。"
                )
                return

            # 更新模型列表
            self.model_combo.clear()
            for model in models:
                self.model_combo.addItem(
                    model.display_name,  # 显示名称
                    model.name  # 实际模型名称作为data
                )

            # 设置当前选中的模型
            current_index = self.model_combo.findData(self.client.model)
            if current_index >= 0:
                self.model_combo.setCurrentIndex(current_index)

            self.model_combo.setEnabled(True)

        except APIError as e:
            self.model_combo.clear()
            self.model_combo.addItem("加载失败")
            self.model_combo.setEnabled(False)

            QMessageBox.critical(
                self,
                "错误",
                f"加载模型列表失败\n\n"
                f"错误信息：{str(e)}\n\n"
                f"请检查：\n"
                f"1. Ollama服务是否正常运行\n"
                f"2. 服务地址 {self.client.base_url} 是否正确\n"
                f"3. 网络连接是否正常\n\n"
                f"您可以：\n"
                f"1. 检查Ollama服务状态\n"
                f"2. 查看服务日志获取详细信息\n"
                f"3. 重启Ollama服务后重试"
            )

    def on_model_changed(self, display_name: str):
        """模型选择改变时的处理"""
        # 获取实际的模型名称
        index = self.model_combo.currentIndex()
        if index >= 0:
            model_name = self.model_combo.itemData(index)
            self.client.set_model(model_name)

            # 可以在这里添加模型切换的动画效果
            # self.chat_widget.show_model_change_animation()

    def new_chat(self):
        """创建新对话"""
        self.chat_widget.clear()
        # 可以在这里添加新对话的动画效果
        # self.chat_widget.show_new_chat_animation()

    def closeEvent(self, event):
        """关闭事件处理"""
        # 确保所有子组件的资源都被正确释放
        if self.chat_widget:
            self.chat_widget.close()
        super().closeEvent(event)