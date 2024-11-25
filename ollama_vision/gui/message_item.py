# ollama_vision/gui/message_item.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor


class MessageItem(QFrame):
    """聊天消息项组件"""

    def __init__(self, content="", role="user", images=None):
        super().__init__()
        self.role = role
        self.content = content
        self.images = images or []

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        # 设置框架样式
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAutoFillBackground(True)

        # 设置背景色和样式
        if self.role == "user":
            self.setStyleSheet("""
                QFrame {
                    background-color: #F7F7F7;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                }
            """)

        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        # 顶部信息区域
        top_layout = QHBoxLayout()

        # 角色图标和标签
        role_layout = QHBoxLayout()
        role_layout.setSpacing(6)

        role_icon = QLabel("👤" if self.role == "user" else "🤖")
        role_icon.setFont(QFont("苹方", 14))
        role_layout.addWidget(role_icon)

        role_label = QLabel("用户" if self.role == "user" else "助手")
        role_label.setFont(QFont("苹方", 11))
        role_label.setStyleSheet("color: #666666;")
        role_layout.addWidget(role_label)

        top_layout.addLayout(role_layout)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # 图片预览区域
        if self.images:
            image_scroll = QScrollArea()
            image_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            image_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            image_scroll.setMaximumHeight(220)
            image_scroll.setWidgetResizable(True)
            image_scroll.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background: transparent;
                }
                QScrollBar:horizontal {
                    height: 8px;
                }
                QScrollBar:handle:horizontal {
                    background: #CCCCCC;
                    border-radius: 4px;
                }
            """)

            image_widget = QWidget()
            image_layout = QHBoxLayout(image_widget)
            image_layout.setContentsMargins(0, 0, 0, 0)
            image_layout.setSpacing(8)

            for image_path in self.images:
                try:
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        # 缩放图片
                        scaled_pixmap = pixmap.scaled(
                            200, 200,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )

                        image_label = QLabel()
                        image_label.setPixmap(scaled_pixmap)
                        image_label.setStyleSheet("""
                            padding: 4px;
                            background: white;
                            border: 1px solid #E0E0E0;
                            border-radius: 4px;
                        """)
                        image_layout.addWidget(image_label)
                except Exception as e:
                    print(f"加载图片失败: {e}")

            image_layout.addStretch()
            image_scroll.setWidget(image_widget)
            main_layout.addWidget(image_scroll)

        # 消息内容
        self.content_label = QLabel(self.content)
        self.content_label.setFont(QFont("苹方", 12))
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.content_label.setStyleSheet("""
            QLabel {
                line-height: 150%;
                color: #333333;
            }
        """)
        self.content_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
        main_layout.addWidget(self.content_label)

        # 添加底部留白
        main_layout.addSpacing(4)

    def append_content(self, text):
        """追加内容文本"""
        current = self.content_label.text()
        self.content_label.setText(current + text)

    def set_error(self, error_msg):
        """设置错误消息"""
        self.content_label.setText(f"发生错误: {error_msg}")
        self.content_label.setStyleSheet("""
            QLabel {
                color: #DC2626;
                line-height: 150%;
            }
        """)

    def sizeHint(self):
        """返回建议大小"""
        width = self.parent().width() if self.parent() else 600
        return QSize(width, self.minimumSizeHint().height())