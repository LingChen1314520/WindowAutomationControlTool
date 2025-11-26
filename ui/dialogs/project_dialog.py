"""项目编辑对话框"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit,
                             QComboBox, QMessageBox, QGroupBox, QCheckBox,
                             QSpinBox)
from PyQt5.QtCore import Qt
from models import Project
from core import WindowManager


class ProjectDialog(QDialog):
    """项目编辑对话框"""

    def __init__(self, parent=None, project: Project = None, groups: dict = None):
        super().__init__(parent)
        self.project = project if project else Project()
        self.is_new = project is None
        self.groups = groups  # 分组参数（即使已移除分组功能，保留接口兼容性防止报错）
        self.window_manager = WindowManager()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setWindowTitle("编辑项目" if not self.is_new else "新建项目")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入项目名称")
        basic_layout.addRow("项目名称:", self.name_edit)

        layout.addWidget(basic_group)

        # 目标窗口
        window_group = QGroupBox("目标窗口")
        window_layout = QFormLayout(window_group)

        select_layout = QHBoxLayout()
        self.window_combo = QComboBox()
        self.window_combo.setMinimumWidth(280)
        select_layout.addWidget(self.window_combo)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedWidth(60)
        # 这里连接了 refresh_windows，确保下面定义了这个方法
        self.refresh_btn.clicked.connect(self.refresh_windows)
        select_layout.addWidget(self.refresh_btn)

        window_layout.addRow("选择窗口:", select_layout)

        self.window_title_edit = QLineEdit()
        self.window_title_edit.setPlaceholderText("窗口标题关键字（用于匹配）")
        window_layout.addRow("窗口标题:", self.window_title_edit)

        self.window_class_edit = QLineEdit()
        self.window_class_edit.setPlaceholderText("可选，用于更精确匹配")
        window_layout.addRow("窗口类名:", self.window_class_edit)

        note = QLabel("💡 操作将在后台执行，不会影响您的鼠标键盘")
        note.setStyleSheet("color: #28a745; font-size: 10px;")
        window_layout.addRow("", note)

        layout.addWidget(window_group)

        # 执行设置
        exec_group = QGroupBox("执行设置")
        exec_layout = QFormLayout(exec_group)

        self.auto_recognize_check = QCheckBox("自动识别场景")
        self.auto_recognize_check.setChecked(True)
        exec_layout.addRow("", self.auto_recognize_check)

        self.recognize_interval_spin = QSpinBox()
        self.recognize_interval_spin.setRange(500, 10000)
        self.recognize_interval_spin.setSingleStep(500)
        self.recognize_interval_spin.setValue(2000)
        self.recognize_interval_spin.setSuffix(" 毫秒")
        exec_layout.addRow("识别间隔:", self.recognize_interval_spin)

        self.loop_check = QCheckBox("循环执行")
        exec_layout.addRow("", self.loop_check)

        self.max_loop_spin = QSpinBox()
        self.max_loop_spin.setRange(0, 9999)
        self.max_loop_spin.setValue(0)
        self.max_loop_spin.setSpecialValueText("无限循环")
        exec_layout.addRow("最大循环:", self.max_loop_spin)

        layout.addWidget(exec_group)

        # 描述
        desc_group = QGroupBox("描述")
        desc_layout = QVBoxLayout(desc_group)
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        self.desc_edit.setPlaceholderText("可选，添加项目说明...")
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
            QPushButton:hover { background-color: #006cc1; }
        """)
        self.ok_btn.clicked.connect(self.on_accept)
        btn_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)

        self.window_combo.currentIndexChanged.connect(self.on_window_selected)
        
        # 初始化时刷新一次窗口
        self.refresh_windows()

    def refresh_windows(self):
        """刷新窗口列表 - 这是之前报错缺失的方法"""
        self.window_combo.blockSignals(True)
        self.window_combo.clear()
        self.window_combo.addItem("-- 选择窗口 --", None)
        
        try:
            windows = self.window_manager.refresh_windows()
            for window in windows:
                text = f"{window.title[:50]}" if len(window.title) <= 50 else f"{window.title[:47]}..."
                self.window_combo.addItem(text, window)
        except Exception as e:
            print(f"刷新窗口失败: {e}")
            
        self.window_combo.blockSignals(False)

    def on_window_selected(self):
        """窗口选择改变"""
        window = self.window_combo.currentData()
        if window:
            self.window_title_edit.setText(window.title)
            self.window_class_edit.setText(window.class_name)

    def load_data(self):
        """加载项目数据"""
        self.name_edit.setText(self.project.name)
        self.window_title_edit.setText(self.project.target_window_title)
        self.window_class_edit.setText(self.project.target_window_class)
        self.desc_edit.setPlainText(self.project.description)
        self.auto_recognize_check.setChecked(self.project.auto_recognize_scene)
        self.recognize_interval_spin.setValue(self.project.recognize_interval)
        self.loop_check.setChecked(self.project.loop_execution)
        self.max_loop_spin.setValue(self.project.max_loop_count)

    def on_accept(self):
        """确定按钮点击"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "警告", "请输入项目名称")
            return
        self.accept()

    def get_project(self) -> Project:
        """获取编辑后的项目"""
        self.project.name = self.name_edit.text().strip()
        self.project.target_window_title = self.window_title_edit.text().strip()
        self.project.target_window_class = self.window_class_edit.text().strip()
        self.project.description = self.desc_edit.toPlainText()
        self.project.auto_recognize_scene = self.auto_recognize_check.isChecked()
        self.project.recognize_interval = self.recognize_interval_spin.value()
        self.project.loop_execution = self.loop_check.isChecked()
        self.project.max_loop_count = self.max_loop_spin.value()
        return self.project