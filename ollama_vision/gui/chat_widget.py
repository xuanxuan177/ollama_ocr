# ollama_vision/gui/chat_widget.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QScrollArea, QFrame, QFileDialog,
    QLabel, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QImageReader

from ollama_vision.client import OllamaVisionClient
from .message_item import MessageItem
from .chat_thread import ChatThread, UploadThread
from .progress_widget import CircularProgressBar


class UploadPreview(QWidget):
    """图片上传预览组件"""

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.encoded_image = None

        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 图片预览
        reader = QImageReader(image_path)
        reader.setScaledSize(QSize(100, 100))
        pixmap = QPixmap.fromImageReader(reader)

        preview = QLabel()
        preview.setFixedSize(100, 100)
        preview.setPixmap(pixmap)
        preview.setScaledContents(True)
        preview.setStyleSheet("""
            QLabel {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        layout.addWidget(preview)

        # 右侧信息区
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # 文件名
        name = QLabel(image_path.split("/")[-1])
        name.setStyleSheet("color: #374151; font-weight: 500;")
        info_layout.addWidget(name)

        # 状态和进度条
        status_layout = QHBoxLayout()
        self.status_label = QLabel("正在上传...")
        self.status_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        status_layout.addWidget(self.status_label)

        self.progress_bar = CircularProgressBar()
        status_layout.addWidget(self.progress_bar)
        status_layout.addStretch()

        info_layout.addLayout(status_layout)
        layout.addLayout(info_layout)
        layout.addStretch()

        # 开始上传
        self.upload_thread = UploadThread(image_path)
        self.upload_thread.progress.connect(self.update_progress)
        self.upload_thread.finished.connect(self.on_upload_complete)
        self.upload_thread.error.connect(self.on_upload_error)
        self.upload_thread.start()

    def update_progress(self, value):
        """更新上传进度"""
        self.progress_bar.setProgress(value)

    def on_upload_complete(self, encoded):
        """上传完成处理"""
        self.encoded_image = encoded
        self.status_label.setText("上传完成")
        self.status_label.setStyleSheet("color: #059669; font-size: 12px;")

    def on_upload_error(self, error):
        """上传错误处理"""
        self.status_label.setText(f"上传失败: {error}")
        self.status_label.setStyleSheet("color: #DC2626; font-size: 12px;")


class ChatWidget(QWidget):
    """聊天组件"""

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.chat_thread = None
        self.uploads = []  # 存储上传预览组件
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 消息展示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: white;
                border: none;
            }
        """)

        self.message_container = QWidget()
        self.messages_layout = QVBoxLayout(self.message_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(16)
        self.messages_layout.setContentsMargins(16, 16, 16, 16)

        self.scroll_area.setWidget(self.message_container)
        layout.addWidget(self.scroll_area)

        # 底部输入区域
        input_container = QWidget()
        input_container.setMaximumHeight(120)
        input_container.setMinimumHeight(100)
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(16, 8, 16, 16)

        # 输入框和按钮
        bottom_layout = QHBoxLayout()

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("输入消息...")
        self.input_box.setMaximumHeight(80)
        self.input_box.textChanged.connect(self.on_input_changed)
        bottom_layout.addWidget(self.input_box)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        self.upload_btn = QPushButton()
        self.upload_btn.setIcon(QIcon.fromTheme("document-open"))
        self.upload_btn.setFixedSize(36, 36)
        self.upload_btn.setToolTip("上传图片")
        self.upload_btn.clicked.connect(self.upload_images)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background: #F3F4F6;
                border: 1px solid #E0E0E0;
                border-radius: 18px;
            }
            QPushButton:hover {
                background: #E5E7EB;
            }
        """)
        btn_layout.addWidget(self.upload_btn)

        self.send_btn = QPushButton()
        self.send_btn.setIcon(QIcon.fromTheme("document-send"))
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.setToolTip("发送")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #2563EB;
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover {
                background: #1D4ED8;
            }
            QPushButton:disabled {
                background: #93C5FD;
            }
        """)
        btn_layout.addWidget(self.send_btn)

        bottom_layout.addLayout(btn_layout)
        input_layout.addLayout(bottom_layout)

        layout.addWidget(input_container)

    def on_input_changed(self):
        """输入框内容改变时的处理"""
        has_text = bool(self.input_box.toPlainText().strip())
        has_uploads = any(upload.encoded_image for upload in self.uploads)
        self.send_btn.setEnabled(has_text and (not self.uploads or has_uploads))

    def upload_images(self):
        """上传图片"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif *.webp)")
        file_dialog.setViewMode(QFileDialog.ViewMode.List)

        if file_dialog.exec():
            filenames = file_dialog.selectedFiles()
            # 添加上传预览到消息区
            for path in filenames:
                preview = UploadPreview(path)
                self.uploads.append(preview)
                self.messages_layout.addWidget(preview)

            # 检查发送按钮状态
            self.on_input_changed()

            # 滚动到底部
            self.scroll_to_bottom()

    def send_message(self):
        """发送消息"""
        text = self.input_box.toPlainText().strip()
        if not text:
            return

        # 检查是否所有图片都上传完成
        encoded_images = []
        for upload in self.uploads:
            if upload.encoded_image:
                encoded_images.append(upload.encoded_image)
            elif upload.upload_thread.isRunning():
                # 等待上传完成
                return

        # 添加用户消息
        user_msg = MessageItem(text, "user", [u.image_path for u in self.uploads])
        self.messages_layout.addWidget(user_msg)

        # 添加助手消息框
        assistant_msg = MessageItem("", "assistant")
        self.messages_layout.addWidget(assistant_msg)

        # 清空输入
        self.input_box.clear()

        # 清理上传组件
        for upload in self.uploads:
            upload.setParent(None)
            upload.deleteLater()
        self.uploads.clear()

        # 创建并启动消息处理线程
        self.chat_thread = ChatThread(
            self.client,
            text,
            encoded_images
        )
        self.chat_thread.response_received.connect(assistant_msg.append_content)
        self.chat_thread.error_occurred.connect(assistant_msg.set_error)
        self.chat_thread.finished.connect(self.on_message_complete)
        self.chat_thread.start()

        # 滚动到底部
        QTimer.singleShot(100, self.scroll_to_bottom)

    def on_message_complete(self):
        """消息处理完成的处理"""
        if self.chat_thread:
            self.chat_thread.deleteLater()
            self.chat_thread = None

        # 滚动到底部
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self):
        """清空聊天记录"""
        # 停止当前的聊天线程
        if self.chat_thread and self.chat_thread.isRunning():
            self.chat_thread.terminate()
            self.chat_thread.wait()
            self.chat_thread.deleteLater()
            self.chat_thread = None

        # 清空消息
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 清空上传
        for upload in self.uploads:
            if upload.upload_thread and upload.upload_thread.isRunning():
                upload.upload_thread.terminate()
                upload.upload_thread.wait()
            upload.deleteLater()
        self.uploads.clear()