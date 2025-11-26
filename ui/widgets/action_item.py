"""操作项组件"""
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QCheckBox, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QFont
from models import Action, ActionType


class ActionItem(QFrame):
    """操作项组件"""
    
    long_pressed = pyqtSignal(str)   # 新增：长按信号
    edit_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    move_up_clicked = pyqtSignal(str)
    move_down_clicked = pyqtSignal(str)
    enabled_changed = pyqtSignal(str, bool)

    def __init__(self, action: Action, index: int, parent=None):
        super().__init__(parent)
        self.action = action
        self.index = index

        self._press_timer = QTimer(self)
        self._press_timer.setSingleShot(True)
        self._press_timer.timeout.connect(self._on_long_press_timeout)
        self._pressed = False
        self._moved = False
        self._press_pos: QPoint = QPoint()

        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel)
        self._update_style()
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # 启用复选框
        self.enabled_check = QCheckBox()
        self.enabled_check.setFixedWidth(18)
        self.enabled_check.setChecked(self.action.enabled)
        self.enabled_check.stateChanged.connect(
            lambda state: self.enabled_changed.emit(self.action.id, state == Qt.Checked)
        )
        layout.addWidget(self.enabled_check)

        # 序号
        self.index_label = QLabel(f"{self.index + 1}")
        self.index_label.setFixedSize(20, 20)
        self.index_label.setStyleSheet("""
            background-color: #0078d4;
            color: white;
            border-radius: 10px;
            font-weight: bold;
            font-size: 9px;
        """)
        self.index_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.index_label)

        # 操作信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)
        info_layout.setContentsMargins(0, 0, 0, 0)

        name_layout = QHBoxLayout()
        name_layout.setSpacing(4)
        
        self.name_label = QLabel(self.action.name or "未命名操作")
        self.name_label.setFont(QFont("", 9, QFont.Bold))
        self.name_label.setStyleSheet("color: #333;")
        name_layout.addWidget(self.name_label)

        self.type_label = QLabel(f"[{ActionType.get_display_name(self.action.action_type)}]")
        self.type_label.setStyleSheet("color: #0078d4; font-size: 8px;")
        name_layout.addWidget(self.type_label)
        name_layout.addStretch()

        info_layout.addLayout(name_layout)

        detail_text = self._get_detail_text()
        self.detail_label = QLabel(detail_text)
        self.detail_label.setStyleSheet("color: #888; font-size: 8px;")
        info_layout.addWidget(self.detail_label)

        layout.addLayout(info_layout, 1)

        # 操作按钮
        btn_style = """
            QPushButton {
                border: 1px solid #ddd;
                border-radius: 3px;
                background: #f8f8f8;
                font-size: 9px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #0078d4;
                color: white;
                border-color: #0078d4;
            }
        """

        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedSize(22, 22)
        self.up_btn.setStyleSheet(btn_style)
        self.up_btn.clicked.connect(lambda: self.move_up_clicked.emit(self.action.id))
        layout.addWidget(self.up_btn)

        self.down_btn = QPushButton("↓")
        self.down_btn.setFixedSize(22, 22)
        self.down_btn.setStyleSheet(btn_style)
        self.down_btn.clicked.connect(lambda: self.move_down_clicked.emit(self.action.id))
        layout.addWidget(self.down_btn)

        self.edit_btn = QPushButton("✎")
        self.edit_btn.setFixedSize(22, 22)
        self.edit_btn.setStyleSheet(btn_style)
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.action.id))
        layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedSize(22, 22)
        self.delete_btn.setStyleSheet(btn_style.replace("#0078d4", "#dc3545"))
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.action.id))
        layout.addWidget(self.delete_btn)

    def _get_detail_text(self) -> str:
        """获取详细信息"""
        action = self.action
        if action.action_type in [ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.RIGHT_CLICK]:
            return f"位置: ({action.relative_x:.3f}, {action.relative_y:.3f})"
        elif action.action_type == ActionType.DRAG:
            return f"({action.relative_x:.2f}, {action.relative_y:.2f}) → ({action.end_relative_x:.2f}, {action.end_relative_y:.2f})"
        elif action.action_type == ActionType.KEY_PRESS:
            return f"按键: {action.key}"
        elif action.action_type == ActionType.INPUT_TEXT:
            text = action.text[:12] + "..." if len(action.text) > 12 else action.text
            return f"文本: {text}"
        elif action.action_type == ActionType.WAIT:
            return f"等待: {action.wait_time}ms"
        return ""

    def _update_style(self):
        """更新样式"""
        if self.action.enabled:
            self.setStyleSheet("""
                ActionItem {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                }
                ActionItem:hover {
                    border-color: #0078d4;
                }
            """)
        else:
            self.setStyleSheet("""
                ActionItem {
                    background-color: #f8f8f8;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                }
            """)

    def update_action(self, action: Action, index: int):
        """更新操作数据"""
        self.action = action
        self.index = index
        self.index_label.setText(f"{index + 1}")
        self.name_label.setText(action.name or "未命名操作")
        self.type_label.setText(f"[{ActionType.get_display_name(action.action_type)}]")
        self.detail_label.setText(self._get_detail_text())
        self.enabled_check.setChecked(action.enabled)
        self._update_style()

    # ------- 长按检测 -------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._moved = False
            self._press_pos = event.pos()
            self._press_timer.start(500)  # 500ms 视为长按
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pressed:
            if (event.pos() - self._press_pos).manhattanLength() > 5:
                self._moved = True
                self._press_timer.stop()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self._press_timer.stop()
        super().mouseReleaseEvent(event)

    def _on_long_press_timeout(self):
        if self._pressed and not self._moved:
            self.long_pressed.emit(self.action.id)