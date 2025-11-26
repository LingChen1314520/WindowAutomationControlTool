"""项目卡片组件"""
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QMenu, QProgressBar, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QFont
from models import Project


class ProjectCard(QFrame):
    """项目卡片 - 支持折叠、双击、长按"""

    # 信号：双击进入编辑，长按用于排序
    double_clicked = pyqtSignal(str)
    long_pressed = pyqtSignal(str)

    edit_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    duplicate_clicked = pyqtSignal(str)
    run_clicked = pyqtSignal(str)
    pause_clicked = pyqtSignal(str)
    stop_clicked = pyqtSignal(str)

    def __init__(self, project: Project, collapsed: bool = True, parent=None):
        super().__init__(parent)
        self.project = project
        self._is_running = False
        self._is_paused = False
        self._collapsed = collapsed

        # 长按检测
        self._press_timer = QTimer(self)
        self._press_timer.setSingleShot(True)
        self._press_timer.timeout.connect(self._on_long_press_timeout)
        self._pressed = False
        self._moved = False
        self._press_pos: QPoint = QPoint()

        self.setup_ui()

    # ---------------- UI 构建 ----------------

    def setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self._update_card_style()
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._update_height()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(10, 8, 10, 8)

        # 标题行
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)

        # 折叠按钮
        self.collapse_btn = QPushButton("▶" if self._collapsed else "▼")
        self.collapse_btn.setFixedSize(18, 18)
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 9px;
                color: #666;
            }
            QPushButton:hover { color: #0078d4; }
        """)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        title_layout.addWidget(self.collapse_btn)

        # 状态点
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: transparent; font-size: 10px;")
        self.status_indicator.setFixedWidth(12)
        title_layout.addWidget(self.status_indicator)

        # 标题
        self.title_label = QLabel(self.project.name)
        self.title_label.setFont(QFont("", 11, QFont.Bold))
        self.title_label.setStyleSheet("color: #333;")
        title_layout.addWidget(self.title_label, 1)

        # 折叠时的简要信息
        self.brief_info = QLabel("")
        self.brief_info.setStyleSheet("color: #888; font-size: 9px;")
        self._update_brief_info()
        title_layout.addWidget(self.brief_info)

        # 快捷运行（只在折叠且未运行时显示）
        self.quick_run_btn = QPushButton("▶")
        self.quick_run_btn.setFixedSize(24, 24)
        self.quick_run_btn.setToolTip("运行项目")
        self.quick_run_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 10px;
            }
            QPushButton:hover { background: #218838; }
        """)
        self.quick_run_btn.clicked.connect(lambda: self.run_clicked.emit(self.project.id))
        title_layout.addWidget(self.quick_run_btn)

        # 更多菜单
        self.more_btn = QPushButton("⋯")
        self.more_btn.setFixedSize(24, 24)
        self.more_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 12px;
                font-size: 12px;
                background: transparent;
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
        self.more_btn.clicked.connect(self.show_menu)
        title_layout.addWidget(self.more_btn)

        self.main_layout.addLayout(title_layout)

        # 详情区域（可折叠）
        self.detail_widget = QFrame()
        self.detail_widget.setStyleSheet("border: none; background: transparent;")
        detail_layout = QVBoxLayout(self.detail_widget)
        detail_layout.setContentsMargins(26, 0, 0, 0)
        detail_layout.setSpacing(5)

        # 描述
        desc_text = self.project.description[:60] + "..." if len(self.project.description) > 60 else self.project.description
        self.desc_label = QLabel(desc_text or "暂无描述")
        self.desc_label.setStyleSheet("color: #666; font-size: 10px;")
        self.desc_label.setWordWrap(True)
        detail_layout.addWidget(self.desc_label)

        # 信息行
        info_layout = QHBoxLayout()
        info_layout.setSpacing(12)
        scene_count = len(self.project.scenes)
        action_count = sum(len(s.actions) for s in self.project.scenes)

        self.info_label = QLabel(f"📑 {scene_count} 场景  ⚡ {action_count} 操作")
        self.info_label.setStyleSheet("color: #888; font-size: 10px;")
        info_layout.addWidget(self.info_label)

        target = self.project.target_window_title
        if target:
            target_display = target[:15] + "..." if len(target) > 15 else target
            self.target_label = QLabel(f"🪟 {target_display}")
            self.target_label.setStyleSheet("color: #888; font-size: 10px;")
            info_layout.addWidget(self.target_label)

        info_layout.addStretch()
        detail_layout.addLayout(info_layout)

        # 进度区域（运行时显示）
        self.progress_widget = QFrame()
        self.progress_widget.setStyleSheet("border: none; background: transparent;")
        progress_layout = QVBoxLayout(self.progress_widget)
        progress_layout.setContentsMargins(0, 2, 0, 0)
        progress_layout.setSpacing(3)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 7px;
                background: #f5f5f5;
                text-align: center;
                font-size: 9px;
            }
            QProgressBar::chunk {
                background: #28a745;
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 9px;")
        progress_layout.addWidget(self.status_label)

        self.progress_widget.hide()
        detail_layout.addWidget(self.progress_widget)

        # 按钮行
        self.btn_widget = QFrame()
        self.btn_widget.setStyleSheet("border: none; background: transparent;")
        btn_layout = QHBoxLayout(self.btn_widget)
        btn_layout.setContentsMargins(0, 3, 0, 0)
        btn_layout.setSpacing(8)

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.setFixedHeight(26)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 3px 12px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.project.id))
        btn_layout.addWidget(self.edit_btn)

        self.run_btn = QPushButton("▶ 运行")
        self.run_btn.setFixedHeight(26)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 3px 12px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        self.run_btn.clicked.connect(lambda: self.run_clicked.emit(self.project.id))
        btn_layout.addWidget(self.run_btn)

        self.pause_btn = QPushButton("⏸ 暂停")
        self.pause_btn.setFixedHeight(26)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #333;
                border: none;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #e0a800; }
        """)
        self.pause_btn.clicked.connect(self._on_pause_click)
        self.pause_btn.hide()
        btn_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setFixedHeight(26)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        self.stop_btn.clicked.connect(lambda: self.stop_clicked.emit(self.project.id))
        self.stop_btn.hide()
        btn_layout.addWidget(self.stop_btn)

        btn_layout.addStretch()
        detail_layout.addWidget(self.btn_widget)

        self.main_layout.addWidget(self.detail_widget)

        self._update_collapse_state()

    # ---------------- 状态更新 ----------------

    def _update_height(self):
        if self._collapsed:
            self.setFixedHeight(40)
        elif self._is_running:
            self.setFixedHeight(175)
        else:
            self.setFixedHeight(145)

    def _update_card_style(self):
        if self._is_running:
            self.setStyleSheet("""
                ProjectCard {
                    background-color: #f0fff0;
                    border: 2px solid #28a745;
                    border-radius: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                ProjectCard {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                }
                ProjectCard:hover { border-color: #0078d4; }
            """)

    def _update_brief_info(self):
        scene_count = len(self.project.scenes)
        action_count = sum(len(s.actions) for s in self.project.scenes)
        self.brief_info.setText(f"({scene_count}场景/{action_count}操作)")

    def _update_collapse_state(self):
        self.detail_widget.setVisible(not self._collapsed)
        self.collapse_btn.setText("▶" if self._collapsed else "▼")
        self.brief_info.setVisible(self._collapsed)
        self.quick_run_btn.setVisible(self._collapsed and not self._is_running)
        self._update_height()

    # ---------------- 交互逻辑 ----------------

    def toggle_collapse(self):
        """点击箭头显隐详情"""
        self._collapsed = not self._collapsed
        self._update_collapse_state()
        self.project.collapsed = self._collapsed

    def set_collapsed(self, collapsed: bool):
        """外部直接设置折叠状态"""
        self._collapsed = collapsed
        self._update_collapse_state()

    def is_collapsed(self) -> bool:
        return self._collapsed

    def show_menu(self):
        """更多菜单（普通右键）"""
        menu = QMenu(self)
        
        if self._collapsed:
            menu.addAction("📂 展开详情").triggered.connect(lambda: self.set_collapsed(False))
        else:
            menu.addAction("📁 折叠").triggered.connect(lambda: self.set_collapsed(True))
        
        menu.addSeparator()
        menu.addAction("📝 编辑项目").triggered.connect(lambda: self.edit_clicked.emit(self.project.id))
        menu.addAction("📋 复制项目").triggered.connect(lambda: self.duplicate_clicked.emit(self.project.id))
        menu.addSeparator()
        menu.addAction("🗑️ 删除项目").triggered.connect(lambda: self.delete_clicked.emit(self.project.id))

        menu.exec_(self.more_btn.mapToGlobal(self.more_btn.rect().bottomLeft()))

    def _on_pause_click(self):
        self.pause_clicked.emit(self.project.id)

    def set_running(self, running: bool):
        """设置运行状态"""
        self._is_running = running
        self._is_paused = False
        
        if running:
            self._collapsed = False
            self.status_indicator.setStyleSheet("color: #28a745; font-size: 10px;")
            self.run_btn.hide()
            self.edit_btn.hide()
            self.pause_btn.show()
            self.stop_btn.show()
            self.progress_widget.show()
            self.status_label.setText("运行中...")
            self.quick_run_btn.hide()
        else:
            self.status_indicator.setStyleSheet("color: transparent; font-size: 10px;")
            self.run_btn.show()
            self.edit_btn.show()
            self.pause_btn.hide()
            self.stop_btn.hide()
            self.progress_widget.hide()
            self.pause_btn.setText("⏸ 暂停")
        
        self._update_card_style()
        self._update_collapse_state()

    def set_paused(self, paused: bool):
        self._is_paused = paused
        if paused:
            self.pause_btn.setText("▶ 继续")
            self.status_label.setText("已暂停")
            self.status_indicator.setStyleSheet("color: #ffc107; font-size: 10px;")
        else:
            self.pause_btn.setText("⏸ 暂停")
            self.status_label.setText("运行中...")
            self.status_indicator.setStyleSheet("color: #28a745; font-size: 10px;")

    def update_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{current}/{total}")

    def update_status(self, message: str):
        if len(message) > 35:
            message = message[:32] + "..."
        self.status_label.setText(message)

    def update_project(self, project: Project):
        self.project = project
        self.title_label.setText(project.name)
        desc_text = project.description[:60] + "..." if len(project.description) > 60 else project.description
        self.desc_label.setText(desc_text or "暂无描述")
        scene_count = len(project.scenes)
        action_count = sum(len(s.actions) for s in project.scenes)
        self.info_label.setText(f"📑 {scene_count} 场景  ⚡ {action_count} 操作")
        self._update_brief_info()

    # ---------------- 鼠标事件：双击 & 长按 ----------------

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
            # 触发“长按”信号，用于 HomePage 弹出排序菜单
            self.long_pressed.emit(self.project.id)

    def mouseDoubleClickEvent(self, event):
        """双击卡片进入项目编辑页面"""
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.project.id)
        super().mouseDoubleClickEvent(event)