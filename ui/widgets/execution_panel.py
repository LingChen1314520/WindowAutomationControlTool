"""执行状态面板组件"""
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                             QProgressBar, QTextEdit, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor
from models import Project
import time


class ExecutionPanel(QFrame):
    """执行状态面板"""

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.project_id = project.id
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            ExecutionPanel {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        self.setFixedHeight(130)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        # 标题行
        header = QHBoxLayout()
        header.setSpacing(6)
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #28a745; font-size: 12px;")
        self.status_indicator.setFixedWidth(14)
        header.addWidget(self.status_indicator)

        self.title_label = QLabel(self.project.name)
        self.title_label.setFont(QFont("", 10, QFont.Bold))
        self.title_label.setStyleSheet("color: #333;")
        header.addWidget(self.title_label)

        header.addStretch()

        self.status_text = QLabel("运行中")
        self.status_text.setStyleSheet("color: #28a745; font-size: 10px;")
        header.addWidget(self.status_text)

        layout.addLayout(header)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 6px;
                background: #f0f0f0;
                text-align: center;
                font-size: 8px;
            }
            QProgressBar::chunk {
                background: #28a745;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 当前操作
        self.action_label = QLabel("准备中...")
        self.action_label.setStyleSheet("color: #666; font-size: 9px;")
        layout.addWidget(self.action_label)

        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(45)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #a0a0a0;
                border: 1px solid #333;
                border-radius: 3px;
                font-family: Consolas, monospace;
                font-size: 8px;
                padding: 2px;
            }
        """)
        layout.addWidget(self.log_text)

    def add_log(self, message: str):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.moveCursor(QTextCursor.End)

    def update_progress(self, current: int, total: int):
        """更新进度"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{current}/{total}")

    def update_action(self, action_name: str):
        """更新当前操作"""
        if len(action_name) > 35:
            action_name = action_name[:32] + "..."
        self.action_label.setText(f"▶ {action_name}")

    def set_status(self, status: str):
        """设置状态"""
        status_config = {
            "running": ("运行中", "#28a745"),
            "paused": ("已暂停", "#ffc107"),
            "stopped": ("已停止", "#dc3545"),
            "finished": ("已完成", "#17a2b8")
        }
        
        text, color = status_config.get(status, ("未知", "#666"))
        self.status_text.setText(text)
        self.status_text.setStyleSheet(f"color: {color}; font-size: 10px;")
        self.status_indicator.setStyleSheet(f"color: {color}; font-size: 12px;")

    def set_finished(self, success: bool, message: str):
        """设置完成状态"""
        self.set_status("finished" if success else "stopped")
        self.action_label.setText(message if len(message) < 40 else message[:37] + "...")
        self.add_log(message)