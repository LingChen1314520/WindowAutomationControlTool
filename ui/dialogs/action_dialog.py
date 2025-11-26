"""操作编辑对话框"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QDoubleSpinBox,
                             QSpinBox, QPushButton, QTextEdit, QGroupBox,
                             QCheckBox)
from PyQt5.QtCore import Qt
from models import Action, ActionType


class ActionDialog(QDialog):
    """操作编辑对话框"""

    def __init__(self, parent=None, action: Action = None):
        super().__init__(parent)
        self.action = action if action else Action()
        self.is_new = action is None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setWindowTitle("编辑操作" if not self.is_new else "新建操作")
        self.setMinimumWidth(450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入操作名称")
        basic_layout.addRow("操作名称:", self.name_edit)

        self.type_combo = QComboBox()
        for action_type in ActionType:
            self.type_combo.addItem(ActionType.get_display_name(action_type), action_type)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        basic_layout.addRow("操作类型:", self.type_combo)

        self.enabled_check = QCheckBox("启用此操作")
        self.enabled_check.setChecked(True)
        basic_layout.addRow("", self.enabled_check)

        layout.addWidget(basic_group)

        # 位置设置
        self.position_group = QGroupBox("位置设置 (相对坐标 0~1)")
        position_layout = QFormLayout(self.position_group)

        hint = QLabel("💡 0.5 表示窗口中心，可通过「拾取位置」功能获取")
        hint.setStyleSheet("color: #666; font-size: 10px;")
        position_layout.addRow(hint)

        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(0, 1)
        self.x_spin.setDecimals(4)
        self.x_spin.setSingleStep(0.01)
        position_layout.addRow("X 坐标:", self.x_spin)

        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(0, 1)
        self.y_spin.setDecimals(4)
        self.y_spin.setSingleStep(0.01)
        position_layout.addRow("Y 坐标:", self.y_spin)

        self.end_x_label = QLabel("终点 X:")
        self.end_x_spin = QDoubleSpinBox()
        self.end_x_spin.setRange(0, 1)
        self.end_x_spin.setDecimals(4)
        self.end_x_spin.setSingleStep(0.01)
        position_layout.addRow(self.end_x_label, self.end_x_spin)

        self.end_y_label = QLabel("终点 Y:")
        self.end_y_spin = QDoubleSpinBox()
        self.end_y_spin.setRange(0, 1)
        self.end_y_spin.setDecimals(4)
        self.end_y_spin.setSingleStep(0.01)
        position_layout.addRow(self.end_y_label, self.end_y_spin)

        layout.addWidget(self.position_group)

        # 输入设置
        self.input_group = QGroupBox("输入设置")
        input_layout = QFormLayout(self.input_group)

        self.key_label = QLabel("按键:")
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("如: enter, ctrl+a, f5")
        input_layout.addRow(self.key_label, self.key_edit)

        self.text_label = QLabel("文本:")
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("要输入的文本内容")
        input_layout.addRow(self.text_label, self.text_edit)

        layout.addWidget(self.input_group)

        # 时间设置
        self.time_group = QGroupBox("时间设置")
        time_layout = QFormLayout(self.time_group)

        self.wait_label = QLabel("等待时间:")
        self.wait_spin = QSpinBox()
        self.wait_spin.setRange(0, 60000)
        self.wait_spin.setSingleStep(100)
        self.wait_spin.setSuffix(" 毫秒")
        time_layout.addRow(self.wait_label, self.wait_spin)

        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 10000)
        self.delay_spin.setSingleStep(50)
        self.delay_spin.setSuffix(" 毫秒")
        self.delay_spin.setValue(300)
        time_layout.addRow("操作后延迟:", self.delay_spin)

        layout.addWidget(self.time_group)

        # 描述
        desc_group = QGroupBox("备注")
        desc_layout = QVBoxLayout(desc_group)
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(50)
        self.desc_edit.setPlaceholderText("可选，添加操作说明...")
        desc_layout.addWidget(self.desc_edit)
        layout.addWidget(desc_group)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.setDefault(True)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #006cc1;
            }
        """)
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        self.on_type_changed()

    def on_type_changed(self):
        """操作类型改变"""
        action_type = self.type_combo.currentData()

        # 位置
        show_position = action_type in [ActionType.CLICK, ActionType.DOUBLE_CLICK,
                                        ActionType.RIGHT_CLICK, ActionType.DRAG]
        self.position_group.setVisible(show_position)

        # 拖拽终点
        show_end = action_type == ActionType.DRAG
        self.end_x_label.setVisible(show_end)
        self.end_x_spin.setVisible(show_end)
        self.end_y_label.setVisible(show_end)
        self.end_y_spin.setVisible(show_end)

        # 按键
        show_key = action_type == ActionType.KEY_PRESS
        self.key_label.setVisible(show_key)
        self.key_edit.setVisible(show_key)

        # 文本
        show_text = action_type == ActionType.INPUT_TEXT
        self.text_label.setVisible(show_text)
        self.text_edit.setVisible(show_text)

        self.input_group.setVisible(show_key or show_text)

        # 等待
        show_wait = action_type == ActionType.WAIT
        self.wait_label.setVisible(show_wait)
        self.wait_spin.setVisible(show_wait)

        self.adjustSize()

    def load_data(self):
        """加载数据"""
        self.name_edit.setText(self.action.name)
        self.enabled_check.setChecked(self.action.enabled)

        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.action.action_type:
                self.type_combo.setCurrentIndex(i)
                break

        self.x_spin.setValue(self.action.relative_x)
        self.y_spin.setValue(self.action.relative_y)
        self.end_x_spin.setValue(self.action.end_relative_x)
        self.end_y_spin.setValue(self.action.end_relative_y)
        self.key_edit.setText(self.action.key)
        self.text_edit.setText(self.action.text)
        self.wait_spin.setValue(self.action.wait_time)
        self.delay_spin.setValue(self.action.delay_after)
        self.desc_edit.setPlainText(self.action.description)

    def get_action(self) -> Action:
        """获取操作"""
        self.action.name = self.name_edit.text() or f"操作_{self.action.id[:6]}"
        self.action.action_type = self.type_combo.currentData()
        self.action.enabled = self.enabled_check.isChecked()
        self.action.relative_x = self.x_spin.value()
        self.action.relative_y = self.y_spin.value()
        self.action.end_relative_x = self.end_x_spin.value()
        self.action.end_relative_y = self.end_y_spin.value()
        self.action.key = self.key_edit.text()
        self.action.text = self.text_edit.text()
        self.action.wait_time = self.wait_spin.value()
        self.action.delay_after = self.delay_spin.value()
        self.action.description = self.desc_edit.toPlainText()
        return self.action