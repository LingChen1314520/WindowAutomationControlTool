"""主页"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QFrame, QGridLayout,
                             QLineEdit, QMessageBox, QSplitter, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QCursor
from core import ProjectManager, ExecutionManager
from models import Project
from .widgets import ProjectCard, ExecutionPanel
from .dialogs import ProjectDialog
from PyQt5.QtWidgets import QMenu          # 新增：弹出菜单
from PyQt5.QtGui import QCursor           # 新增：获取鼠标位置


class HomePage(QWidget):
    """主页"""
    
    project_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_manager = ProjectManager()
        self.execution_manager = ExecutionManager()
        self.project_cards = {}  # project_id -> ProjectCard
        self.execution_panels = {}  # project_id -> ExecutionPanel
        self.setup_ui()
        self.connect_signals()
        self.load_projects()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部区域
        header = QFrame()
        header.setStyleSheet("background-color: white; border-bottom: 1px solid #e0e0e0;")
        header.setFixedHeight(70)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("窗口自动化控制工具")
        title.setFont(QFont("", 20, QFont.Bold))
        title.setStyleSheet("color: #333; border: none;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索项目...")
        self.search_edit.setFixedWidth(200)
        self.search_edit.setFixedHeight(36)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 18px;
                padding: 8px 15px;
                font-size: 12px;
                background: #f5f5f5;
            }
            QLineEdit:focus {
                border-color: #0078d4;
                background: white;
            }
        """)
        self.search_edit.textChanged.connect(self.filter_projects)
        header_layout.addWidget(self.search_edit)

        # 新建项目按钮
        self.new_btn = QPushButton("+ 新建项目")
        self.new_btn.setFixedHeight(36)
        self.new_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 18px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #006cc1;
            }
        """)
        self.new_btn.clicked.connect(self.create_project)
        header_layout.addWidget(self.new_btn)

        layout.addWidget(header)

        # 主内容区
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet("""
            QSplitter { background: #f5f5f5; }
            QSplitter::handle {
                background: #e0e0e0;
                width: 3px;
            }
            QSplitter::handle:hover {
                background: #0078d4;
            }
        """)

        # 左侧 - 项目列表
        left_panel = QFrame()
        left_panel.setStyleSheet("background: #f5f5f5; border: none;")
        left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 10, 15)
        left_layout.setSpacing(10)

        # 统计和操作
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.total_label = self._create_stat_label("项目", "0")
        stats_layout.addWidget(self.total_label)
        
        self.running_label = self._create_stat_label("运行中", "0")
        stats_layout.addWidget(self.running_label)
        
        stats_layout.addStretch()
        
        # 全部展开/折叠按钮
        self.expand_all_btn = QPushButton("全部展开")
        self.expand_all_btn.setFixedHeight(28)
        self.expand_all_btn.setStyleSheet("""
            QPushButton {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover { background: #f0f0f0; border-color: #0078d4; }
        """)
        self.expand_all_btn.clicked.connect(self.expand_all)
        stats_layout.addWidget(self.expand_all_btn)
        
        self.collapse_all_btn = QPushButton("全部折叠")
        self.collapse_all_btn.setFixedHeight(28)
        self.collapse_all_btn.setStyleSheet("""
            QPushButton {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover { background: #f0f0f0; border-color: #0078d4; }
        """)
        self.collapse_all_btn.clicked.connect(self.collapse_all)
        stats_layout.addWidget(self.collapse_all_btn)
        
        left_layout.addLayout(stats_layout)

        # 项目列表滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.projects_widget = QWidget()
        self.projects_widget.setStyleSheet("background: transparent;")
        self.projects_layout = QVBoxLayout(self.projects_widget)
        self.projects_layout.setSpacing(8)
        self.projects_layout.setContentsMargins(0, 0, 10, 0)
        self.projects_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.projects_widget)
        left_layout.addWidget(scroll)

        self.splitter.addWidget(left_panel)

        # 右侧 - 运行状态面板
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background: white;
                border-left: 1px solid #e0e0e0;
            }
        """)
        right_panel.setMinimumWidth(280)
        right_panel.setMaximumWidth(400)
        right_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(10)

        right_header = QHBoxLayout()
        right_title = QLabel("运行状态")
        right_title.setFont(QFont("", 14, QFont.Bold))
        right_title.setStyleSheet("border: none;")
        right_header.addWidget(right_title)
        
        right_header.addStretch()
        
        self.stop_all_btn = QPushButton("全部停止")
        self.stop_all_btn.setFixedHeight(28)
        self.stop_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #c82333; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.stop_all_btn.clicked.connect(self.stop_all_projects)
        self.stop_all_btn.setEnabled(False)
        right_header.addWidget(self.stop_all_btn)
        
        right_layout.addLayout(right_header)

        self.execution_scroll = QScrollArea()
        self.execution_scroll.setWidgetResizable(True)
        self.execution_scroll.setFrameShape(QFrame.NoFrame)
        self.execution_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.execution_scroll.setStyleSheet("border: none; background: transparent;")

        self.execution_widget = QWidget()
        self.execution_widget.setStyleSheet("background: transparent;")
        self.execution_layout = QVBoxLayout(self.execution_widget)
        self.execution_layout.setSpacing(10)
        self.execution_layout.setContentsMargins(0, 0, 0, 0)
        self.execution_layout.setAlignment(Qt.AlignTop)

        self.no_running_label = QLabel("暂无运行中的项目\n\n点击项目的「▶」按钮开始运行")
        self.no_running_label.setAlignment(Qt.AlignCenter)
        self.no_running_label.setStyleSheet("color: #999; font-size: 12px;")
        self.execution_layout.addWidget(self.no_running_label)
        self.execution_layout.addStretch()

        self.execution_scroll.setWidget(self.execution_widget)
        right_layout.addWidget(self.execution_scroll)

        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([750, 320])
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter)

    def _create_stat_label(self, title: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        frame.setFixedSize(90, 55)

        layout = QVBoxLayout(frame)
        layout.setSpacing(2)
        layout.setContentsMargins(10, 5, 10, 5)

        value_label = QLabel(value)
        value_label.setFont(QFont("", 16, QFont.Bold))
        value_label.setStyleSheet("color: #0078d4; border: none;")
        value_label.setObjectName("value")
        layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 10px; border: none;")
        layout.addWidget(title_label)

        return frame

    def connect_signals(self):
        self.execution_manager.project_started.connect(self.on_project_started)
        self.execution_manager.project_stopped.connect(self.on_project_stopped)
        self.execution_manager.project_log.connect(self.on_project_log)
        self.execution_manager.project_progress.connect(self.on_project_progress)
        self.execution_manager.project_status.connect(self.on_project_status)
        self.execution_manager.project_finished.connect(self.on_project_finished)

    def load_projects(self):
        """加载项目列表"""
        # 清除现有卡片
        for card in self.project_cards.values():
            card.deleteLater()
        self.project_cards.clear()

        while self.projects_layout.count():
            item = self.projects_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projects = self.project_manager.get_all_projects()

        if not projects:
            empty_label = QLabel("暂无项目\n点击「新建项目」开始创建")
            empty_label.setStyleSheet("color: #999; font-size: 13px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.projects_layout.addWidget(empty_label)
        else:
            for project in projects:
                is_running = self.execution_manager.is_running(project.id)
                collapsed = project.collapsed if not is_running else False

                card = ProjectCard(project, collapsed=collapsed)
                # 双击进入编辑
                card.double_clicked.connect(self.project_selected.emit)
                # 长按弹出排序菜单
                card.long_pressed.connect(self.on_project_long_pressed)

                # 其他信号保持不变
                card.edit_clicked.connect(self.project_selected.emit)
                card.delete_clicked.connect(self.delete_project)
                card.duplicate_clicked.connect(self.duplicate_project)
                card.run_clicked.connect(self.run_project)
                card.pause_clicked.connect(self.toggle_pause_project)
                card.stop_clicked.connect(self.stop_project)

                if is_running:
                    card.set_running(True)
                    if self.execution_manager.is_paused(project.id):
                        card.set_paused(True)

                self.projects_layout.addWidget(card)
                self.project_cards[project.id] = card

            self.projects_layout.addStretch()

        self._update_stats()

    def _update_stats(self):
        total = len(self.project_manager.get_all_projects())
        running = len(self.execution_manager.get_running_projects())
        
        self.total_label.findChild(QLabel, "value").setText(str(total))
        self.running_label.findChild(QLabel, "value").setText(str(running))
        self.stop_all_btn.setEnabled(running > 0)

    def filter_projects(self, text: str):
        text = text.lower()
        for project_id, card in self.project_cards.items():
            project = self.project_manager.get_project(project_id)
            if project:
                visible = (text in project.name.lower() or 
                          text in project.description.lower())
                card.setVisible(visible)

    def expand_all(self):
        for card in self.project_cards.values():
            card.set_collapsed(False)

    def collapse_all(self):
        for card in self.project_cards.values():
            if not card._is_running:
                card.set_collapsed(True)

    def create_project(self):
        dialog = ProjectDialog(self)
        if dialog.exec_() == ProjectDialog.Accepted:
            project_data = dialog.get_project()
            project = self.project_manager.create_project(
                name=project_data.name,
                description=project_data.description,
                target_window_title=project_data.target_window_title
            )
            project.target_window_class = project_data.target_window_class
            project.auto_recognize_scene = project_data.auto_recognize_scene
            project.recognize_interval = project_data.recognize_interval
            project.loop_execution = project_data.loop_execution
            project.max_loop_count = project_data.max_loop_count
            self.project_manager.save_project(project)
            self.load_projects()
            self.project_selected.emit(project.id)

    def delete_project(self, project_id: str):
        if self.execution_manager.is_running(project_id):
            QMessageBox.warning(self, "警告", "项目正在运行中，请先停止")
            return

        project = self.project_manager.get_project(project_id)
        if not project:
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除项目「{project.name}」吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.project_manager.delete_project(project_id)
            self.load_projects()

    def duplicate_project(self, project_id: str):
        new_project = self.project_manager.duplicate_project(project_id)
        if new_project:
            self.load_projects()
            QMessageBox.information(self, "成功", f"已创建副本「{new_project.name}」")

    def run_project(self, project_id: str):
        project = self.project_manager.get_project(project_id)
        if not project:
            return

        if self.execution_manager.is_running(project_id):
            QMessageBox.information(self, "提示", "项目已在运行中")
            return

        success, message = self.execution_manager.start_project(project)
        
        if success:
            self._create_execution_panel(project)
            if project_id in self.project_cards:
                self.project_cards[project_id].set_running(True)
            self._update_stats()
        else:
            QMessageBox.warning(self, "启动失败", message)

    def _create_execution_panel(self, project: Project):
        self.no_running_label.hide()
        panel = ExecutionPanel(project)
        self.execution_layout.insertWidget(0, panel)
        self.execution_panels[project.id] = panel

    def _remove_execution_panel(self, project_id: str):
        if project_id in self.execution_panels:
            self.execution_panels[project_id].deleteLater()
            del self.execution_panels[project_id]
        if not self.execution_panels:
            self.no_running_label.show()

    def stop_project(self, project_id: str):
        self.execution_manager.stop_project(project_id)

    def toggle_pause_project(self, project_id: str):
        if self.execution_manager.is_paused(project_id):
            self.execution_manager.resume_project(project_id)
            if project_id in self.project_cards:
                self.project_cards[project_id].set_paused(False)
        else:
            self.execution_manager.pause_project(project_id)
            if project_id in self.project_cards:
                self.project_cards[project_id].set_paused(True)

    def stop_all_projects(self):
        running = self.execution_manager.get_running_projects()
        if not running:
            return
            
        reply = QMessageBox.question(
            self, "确认",
            f"确定要停止所有 {len(running)} 个运行中的项目吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.execution_manager.stop_all()

    def on_project_started(self, project_id: str):
        self._update_stats()

    def on_project_stopped(self, project_id: str):
        if project_id in self.project_cards:
            self.project_cards[project_id].set_running(False)
        self._update_stats()

    def on_project_log(self, project_id: str, message: str):
        if project_id in self.execution_panels:
            self.execution_panels[project_id].add_log(message)
        if project_id in self.project_cards:
            self.project_cards[project_id].update_status(message)

    def on_project_progress(self, project_id: str, current: int, total: int):
        if project_id in self.execution_panels:
            self.execution_panels[project_id].update_progress(current, total)
        if project_id in self.project_cards:
            self.project_cards[project_id].update_progress(current, total)

    def on_project_status(self, project_id: str, status: str):
        if project_id in self.execution_panels:
            self.execution_panels[project_id].set_status(status)
        if project_id in self.project_cards:
            if status == "paused":
                self.project_cards[project_id].set_paused(True)
            elif status == "running":
                self.project_cards[project_id].set_paused(False)

    def on_project_finished(self, project_id: str, success: bool, message: str):
        if project_id in self.execution_panels:
            self.execution_panels[project_id].set_finished(success, message)
        if project_id in self.project_cards:
            self.project_cards[project_id].set_running(False)
        self._update_stats()
        QTimer.singleShot(5000, lambda pid=project_id: self._remove_execution_panel(pid))

    def refresh(self):
        """刷新"""
        self.project_manager.load_all_projects()
        self.load_projects()

    def on_project_long_pressed(self, project_id: str):
        """长按项目卡片，弹出上移/下移菜单"""
        menu = QMenu(self)
        up_action = menu.addAction("上移项目")
        down_action = menu.addAction("下移项目")

        chosen = menu.exec_(QCursor.pos())
        if not chosen:
            return

        if chosen == up_action:
            self.project_manager.move_project(project_id, -1)
        elif chosen == down_action:
            self.project_manager.move_project(project_id, 1)

        # 重新加载列表以反映新顺序
        self.load_projects()