# ui/dialogs/anchor_capture_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QRubberBand)
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPixmap, QImage
from core import WindowManager


class AnchorCaptureDialog(QDialog):
    """
    从当前窗口截图中框选一个矩形区域，作为锚点模板。
    返回：选区在图像中的像素矩形 + 原始图像尺寸（用于计算 ROI）。
    """

    def __init__(self, hwnd: int, parent=None):
        super().__init__(parent)
        self.hwnd = hwnd
        self.window_manager = WindowManager()
        self.setWindowTitle("选择锚点区域")
        self.resize(800, 600)

        self._pixmap = None
        self._rubber_band = None
        self._origin = QPoint()
        self._selection_rect = QRect()

        self._setup_ui()
        self._load_screenshot()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        tip = QLabel("在图像上按下并拖动鼠标，选择锚点区域。")
        tip.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(tip)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll, 1)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMouseTracking(True)
        self.scroll.setWidget(self.image_label)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def _load_screenshot(self):
        """截取窗口并显示"""
        pil_image = self.window_manager.capture_window(self.hwnd)
        if not pil_image:
            self.image_label.setText("无法截取窗口图像")
            self.ok_btn.setEnabled(False)
            return

        pil_image = pil_image.convert("RGB")
        w, h = pil_image.size
        data = pil_image.tobytes("raw", "RGB")
        qimage = QImage(data, w, h, QImage.Format_RGB888)
        self._pixmap = QPixmap.fromImage(qimage)

        self.image_label.setPixmap(self._pixmap)
        self.image_label.resize(self._pixmap.size())

    # ------- 安装在 image_label 上的鼠标事件 -------

    def image_label_mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._pixmap:
            self._origin = event.pos()
            if not self._rubber_band:
                self._rubber_band = QRubberBand(QRubberBand.Rectangle, self.image_label)
            # 这里改用 origin, origin，不再用 QSize()
            self._rubber_band.setGeometry(QRect(self._origin, self._origin))
            self._rubber_band.show()

    def image_label_mouseMoveEvent(self, event):
        if self._rubber_band and self._pixmap:
            rect = QRect(self._origin, event.pos()).normalized()
            self._rubber_band.setGeometry(rect)

    def image_label_mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._rubber_band and self._pixmap:
            self._selection_rect = self._rubber_band.geometry()
            self._rubber_band.hide()

    def accept(self):
        # 确保有有效选区
        if (not self._pixmap or
                self._selection_rect.isNull() or
                self._selection_rect.width() < 3 or
                self._selection_rect.height() < 3):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "请先在图像上框选一个区域作为锚点。")
            return
        super().accept()

    def get_result(self):
        """
        返回 (rect, image_width, image_height)
        rect 是在截图坐标系下的 QRect
        """
        if not self._pixmap:
            return None, 0, 0
        return self._selection_rect, self._pixmap.width(), self._pixmap.height()

    def showEvent(self, event):
        """在对话框显示时，把鼠标事件绑定到 image_label 上"""
        super().showEvent(event)
        self.image_label.mousePressEvent = self.image_label_mousePressEvent
        self.image_label.mouseMoveEvent = self.image_label_mouseMoveEvent
        self.image_label.mouseReleaseEvent = self.image_label_mouseReleaseEvent