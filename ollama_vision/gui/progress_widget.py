# ollama_vision/gui/progress_widget.py

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen


class CircularProgressBar(QWidget):
    """圆形进度条组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0
        self.setFixedSize(40, 40)

    def setProgress(self, value):
        """设置进度值(0-100)"""
        self.progress = int(min(max(0, value), 100))
        self.update()  # 触发重绘

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 计算圆形区域
        pen_width = 3
        rect = QRect(
            int(pen_width / 2),
            int(pen_width / 2),
            self.width() - pen_width,
            self.height() - pen_width
        )

        # 绘制背景圆环
        painter.setPen(QPen(QColor("#E5E7EB"), pen_width))
        painter.drawArc(rect, 0, 360 * 16)  # Qt中角度需要乘16

        # 绘制进度圆环
        if self.progress > 0:
            painter.setPen(QPen(QColor("#2563EB"), pen_width))
            # 确保使用整数
            span_angle = int((-self.progress * 360 * 16) / 100)
            painter.drawArc(rect, 90 * 16, span_angle)

        # 如果进度为100%,绘制完成对勾
        if self.progress >= 100:
            painter.setPen(QPen(QColor("#059669"), pen_width))
            center_x = int(rect.center().x())
            center_y = int(rect.center().y())
            # 绘制对勾
            painter.drawLine(
                center_x - 8, center_y,
                center_x - 3, center_y + 5
            )
            painter.drawLine(
                center_x - 3, center_y + 5,
                center_x + 8, center_y - 6
            )