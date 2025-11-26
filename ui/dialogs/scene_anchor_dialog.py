# ui/dialogs/scene_anchor_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel,
                             QLineEdit, QDoubleSpinBox, QPushButton,
                             QHBoxLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from models import SceneAnchor


class SceneAnchorDialog(QDialog):
    """锚点属性编辑对话框：名称 + 阈值 + 预览"""

    def __init__(self, parent=None, anchor: SceneAnchor = None):
        super().__init__(parent)
        self.anchor = anchor if anchor else SceneAnchor()
        self.is_new = anchor is None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("编辑锚点" if not self.is_new else "新建锚点")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如：登录按钮 / 设置图标")
        form.addRow("锚点名称:", self.name_edit)

        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.5, 1.0)
        self.threshold_spin.setDecimals(2)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.setValue(0.85)
        form.addRow("匹配阈值:", self.threshold_spin)

        tip = QLabel("值越高匹配越严格，建议 0.80 ~ 0.95")
        tip.setStyleSheet("color: #666; font-size: 10px;")
        form.addRow("", tip)

        layout.addLayout(form)

        # 预览小图
        self.preview_label = QLabel("无预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(100)
        self.preview_label.setStyleSheet("border: 1px solid #ddd; background: #f8f8f8;")
        layout.addWidget(self.preview_label)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _load_data(self):
        self.name_edit.setText(self.anchor.name)
        self.threshold_spin.setValue(self.anchor.threshold)

        if self.anchor.image_path:
            from PyQt5.QtGui import QPixmap
            pix = QPixmap(self.anchor.image_path)
            if not pix.isNull():
                scaled = pix.scaled(200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled)
                self.preview_label.setText("")
            else:
                self.preview_label.setText("预览失败")

    def get_anchor(self) -> SceneAnchor:
        self.anchor.name = self.name_edit.text().strip() or "锚点"
        self.anchor.threshold = self.threshold_spin.value()
        return self.anchor