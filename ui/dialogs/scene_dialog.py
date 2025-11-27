# ui/dialogs/scene_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QDoubleSpinBox, QPushButton,
                             QTextEdit, QCheckBox, QFileDialog, QGroupBox,
                             QListWidget, QListWidgetItem, QMessageBox)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from models import Scene, SceneAnchor
from .anchor_capture_dialog import AnchorCaptureDialog
from .scene_anchor_dialog import SceneAnchorDialog
import os


class SceneDialog(QDialog):
    """场景编辑对话框（带锚点管理）"""

    def __init__(self, parent=None, scene: Scene = None,
                 project=None, hwnd: int = None, image_dir: str = ""):
        """
        hwnd: 当前项目对应窗口的句柄（用于截图）
        image_dir: 项目图片目录，用于保存场景图和锚点图
        """
        super().__init__(parent)
        self.scene = scene if scene else Scene()
        self.is_new = scene is None
        self.project = project
        self.hwnd = hwnd
        self.image_dir = image_dir
        self._setup_ui()
        self._load_scene_data()

    def _setup_ui(self):
        self.setWindowTitle("编辑场景" if not self.is_new else "新建场景")
        self.setMinimumWidth(520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # -------- 基本信息 --------
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入场景名称")
        basic_layout.addRow("场景名称:", self.name_edit)

        self.enabled_check = QCheckBox("启用此场景")
        self.enabled_check.setChecked(True)
        basic_layout.addRow("", self.enabled_check)

        self.default_check = QCheckBox("设为默认场景")
        basic_layout.addRow("", self.default_check)

        layout.addWidget(basic_group)

        # -------- 场景整图识别设置（保留原来的） --------
        recognition_group = QGroupBox("整图识别设置（可选）")
        recognition_layout = QVBoxLayout(recognition_group)

        image_layout = QHBoxLayout()
        self.image_label = QLabel("未选择图片")
        self.image_label.setFixedSize(180, 120)
        self.image_label.setStyleSheet("""
            border: 2px dashed #ccc;
            background: #f9f9f9;
            border-radius: 5px;
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.image_label)

        image_btn_layout = QVBoxLayout()
        self.select_image_btn = QPushButton("选择整图")
        self.select_image_btn.clicked.connect(self.select_image)
        image_btn_layout.addWidget(self.select_image_btn)

        self.clear_image_btn = QPushButton("清除整图")
        self.clear_image_btn.clicked.connect(self.clear_image)
        image_btn_layout.addWidget(self.clear_image_btn)
        image_btn_layout.addStretch()

        image_layout.addLayout(image_btn_layout)
        recognition_layout.addLayout(image_layout)

        threshold_layout = QFormLayout()
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 1.0)
        self.threshold_spin.setDecimals(2)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.setValue(0.8)
        threshold_layout.addRow("整图识别阈值:", self.threshold_spin)

        threshold_hint = QLabel("整图匹配的阈值（锚点优先，整图兜底）")
        threshold_hint.setStyleSheet("color: #666; font-size: 10px;")
        threshold_layout.addRow("", threshold_hint)

        recognition_layout.addLayout(threshold_layout)
        layout.addWidget(recognition_group)

        # -------- 锚点识别设置 --------
        anchor_group = QGroupBox("识别锚点（推荐）")
        anchor_layout = QVBoxLayout(anchor_group)

        tip = QLabel("你可以为该场景添加一个或多个锚点（按钮/图标/文字区域）。\n"
                     "识别时，优先用锚点进行局部匹配。")
        tip.setStyleSheet("color: #666; font-size: 10px;")
        anchor_layout.addWidget(tip)

        self.anchor_list = QListWidget()
        self.anchor_list.setMinimumHeight(100)
        anchor_layout.addWidget(self.anchor_list)

        btn_row = QHBoxLayout()
        self.add_anchor_btn = QPushButton("添加锚点")
        self.add_anchor_btn.clicked.connect(self.add_anchor)
        btn_row.addWidget(self.add_anchor_btn)

        self.edit_anchor_btn = QPushButton("编辑锚点")
        self.edit_anchor_btn.clicked.connect(self.edit_anchor)
        btn_row.addWidget(self.edit_anchor_btn)

        self.remove_anchor_btn = QPushButton("删除锚点")
        self.remove_anchor_btn.clicked.connect(self.remove_anchor)
        btn_row.addWidget(self.remove_anchor_btn)

        btn_row.addStretch()
        anchor_layout.addLayout(btn_row)

        layout.addWidget(anchor_group)

        # -------- 描述 --------
        desc_group = QGroupBox("描述")
        desc_layout = QVBoxLayout(desc_group)
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        self.desc_edit.setPlaceholderText("可选，添加场景说明...")
        desc_layout.addWidget(self.desc_edit)
        layout.addWidget(desc_group)

        # -------- 按钮 --------
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("确定")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        # 如果没有 hwnd（当前项目没有找到窗口），禁用锚点添加
        if self.hwnd is None:
            self.add_anchor_btn.setEnabled(False)
            self.add_anchor_btn.setToolTip("当前未连接到目标窗口，无法截取锚点。")

    def _load_scene_data(self):
        self.name_edit.setText(self.scene.name)
        self.enabled_check.setChecked(self.scene.enabled)
        self.default_check.setChecked(self.scene.is_default)
        self.threshold_spin.setValue(self.scene.recognition_threshold)
        self.desc_edit.setPlainText(self.scene.description)

        # 整图预览
        if self.scene.recognition_image_path and os.path.exists(self.scene.recognition_image_path):
            self._show_image(self.scene.recognition_image_path)

        # # 默认场景不能取消默认标记（编辑时）
        # if self.scene.is_default and not self.is_new:
        #     self.default_check.setEnabled(False)

        # 加载锚点列表
        self._refresh_anchor_list()

    # ------- 整图操作 -------

    def select_image(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择识别整图", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if filepath:
            self.scene.recognition_image_path = filepath
            self._show_image(filepath)

    def clear_image(self):
        self.scene.recognition_image_path = None
        self.image_label.setText("未选择图片")
        self.image_label.setPixmap(QPixmap())

    def _show_image(self, filepath: str):
        pix = QPixmap(filepath)
        if not pix.isNull():
            scaled = pix.scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            self.image_label.setText("")
        else:
            self.image_label.setText("图片加载失败")

    # ------- 锚点列表 -------

    def _refresh_anchor_list(self):
        self.anchor_list.clear()
        for anchor in self.scene.anchors:
            text = f"{anchor.name or '锚点'}  (阈值:{anchor.threshold:.2f})"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, anchor.id)
            self.anchor_list.addItem(item)

    def _find_anchor(self, anchor_id: str) -> SceneAnchor:
        for a in self.scene.anchors:
            if a.id == anchor_id:
                return a
        return None

    def add_anchor(self):
        """添加锚点：截图 -> 框选区域 -> 保存小图 -> 编辑属性"""
        if self.hwnd is None:
            QMessageBox.warning(self, "提示", "当前未连接到目标窗口，无法截取锚点。")
            return

        # 1. 弹出裁剪对话框
        cap_dialog = AnchorCaptureDialog(self.hwnd, self)
        if cap_dialog.exec_() != QDialog.Accepted:
            return

        rect, img_w, img_h = cap_dialog.get_result()
        if not rect or rect.isNull():
            return

        # 2. 计算 ROI（相对坐标）
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        roi_x = x / img_w
        roi_y = y / img_h
        roi_w = w / img_w
        roi_h = h / img_h

        # 3. 从截图中裁剪小图并保存
        # 重新从 WindowManager 捕获一次，保证和 SceneManager 使用的一致
        from core import WindowManager
        wm = WindowManager()
        pil_image = wm.capture_window(self.hwnd)
        if not pil_image:
            QMessageBox.warning(self, "错误", "截取窗口失败，无法生成锚点图。")
            return
        pil_image = pil_image.convert("RGB")
        crop_box = (x, y, x + w, y + h)
        cropped = pil_image.crop(crop_box)

        # 保存到项目图片目录
        import os, uuid
        os.makedirs(self.image_dir, exist_ok=True)
        fname = f"anchor_{self.scene.id}_{uuid.uuid4().hex[:8]}.png"
        save_path = os.path.join(self.image_dir, fname)
        cropped.save(save_path)

        # 4. 创建锚点对象
        anchor = SceneAnchor(
            name="锚点",
            image_path=save_path,
            threshold=0.85,
            roi_x=roi_x,
            roi_y=roi_y,
            roi_w=roi_w,
            roi_h=roi_h,
        )

        # 5. 弹出属性对话框让用户调整名称和阈值
        attr_dialog = SceneAnchorDialog(self, anchor)
        if attr_dialog.exec_() == QDialog.Accepted:
            anchor = attr_dialog.get_anchor()
            self.scene.anchors.append(anchor)
            self._refresh_anchor_list()

    def edit_anchor(self):
        item = self.anchor_list.currentItem()
        if not item:
            return
        anchor_id = item.data(Qt.UserRole)
        anchor = self._find_anchor(anchor_id)
        if not anchor:
            return

        dialog = SceneAnchorDialog(self, anchor)
        if dialog.exec_() == QDialog.Accepted:
            dialog.get_anchor()
            self._refresh_anchor_list()

    def remove_anchor(self):
        item = self.anchor_list.currentItem()
        if not item:
            return
        anchor_id = item.data(Qt.UserRole)
        anchor = self._find_anchor(anchor_id)
        if not anchor:
            return

        if QMessageBox.question(self, "确认删除", f"删除锚点「{anchor.name or '锚点'}」？") == QMessageBox.Yes:
            self.scene.anchors = [a for a in self.scene.anchors if a.id != anchor_id]
            self._refresh_anchor_list()

    def get_scene(self) -> Scene:
        """收集对话框中的修改"""
        self.scene.name = self.name_edit.text().strip() or "未命名场景"
        self.scene.enabled = self.enabled_check.isChecked()
        self.scene.is_default = self.default_check.isChecked()
        self.scene.recognition_threshold = self.threshold_spin.value()
        self.scene.description = self.desc_edit.toPlainText()
        return self.scene