"""项目编辑页"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTreeWidget, QTreeWidgetItem,
                             QScrollArea, QFrame, QMessageBox, QMenu,
                             QGroupBox, QSplitter, QSizePolicy,QDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QImage, QCursor
from core import ProjectManager, WindowManager, SceneManager
from models import Project, Scene, Action
from .widgets import ActionItem
from .dialogs import ProjectDialog, SceneDialog, ActionDialog
from PyQt5.QtWidgets import QMenu          # 新增：弹出菜单
from PyQt5.QtGui import QCursor           # 新增：获取鼠标位置

class ProjectPage(QWidget):
    """项目编辑页"""
    
    back_clicked = pyqtSignal()
    run_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_manager = ProjectManager()
        self.window_manager = WindowManager()
        self.scene_manager = SceneManager()
        
        self.current_project: Project = None
        self.current_scene: Scene = None
        self.current_window = None
        self.action_items = []
        self._picking_position = False
        self._preview_pixmap = None
        
        self.setup_ui()
        
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部导航栏
        nav = QFrame()
        nav.setStyleSheet("background: white; border-bottom: 1px solid #e0e0e0;")
        nav.setFixedHeight(55)
        
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(15, 0, 15, 0)

        self.back_btn = QPushButton("← 返回")
        self.back_btn.setStyleSheet("""
            QPushButton {
                border: none;
                color: #0078d4;
                font-size: 13px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: #f0f0f0;
                border-radius: 4px;
            }
        """)
        self.back_btn.clicked.connect(self.on_back)
        nav_layout.addWidget(self.back_btn)

        self.title_label = QLabel("项目")
        self.title_label.setFont(QFont("", 14, QFont.Bold))
        nav_layout.addWidget(self.title_label)

        nav_layout.addStretch()

        self.settings_btn = QPushButton("⚙ 设置")
        self.settings_btn.clicked.connect(self.edit_settings)
        nav_layout.addWidget(self.settings_btn)

        self.run_btn = QPushButton("▶ 运行")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 18px;
                font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        self.run_btn.clicked.connect(self.on_run)
        nav_layout.addWidget(self.run_btn)

        layout.addWidget(nav)

        # 内容区 - 使用QSplitter实现自适应
        content = QWidget()
        content.setStyleSheet("background: #f5f5f5;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background: #e0e0e0;
                width: 3px;
            }
            QSplitter::handle:hover {
                background: #0078d4;
            }
        """)

        # 左侧 - 场景面板
        left_panel = self._create_scene_panel()
        left_panel.setMinimumWidth(180)
        left_panel.setMaximumWidth(300)
        self.splitter.addWidget(left_panel)

        # 中间 - 操作面板
        middle_panel = self._create_action_panel()
        middle_panel.setMinimumWidth(250)
        self.splitter.addWidget(middle_panel)

        # 右侧 - 预览面板
        right_panel = self._create_preview_panel()
        right_panel.setMinimumWidth(280)
        self.splitter.addWidget(right_panel)

        self.splitter.setSizes([200, 350, 350])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setStretchFactor(2, 2)

        content_layout.addWidget(self.splitter)
        layout.addWidget(content)

    def _create_scene_panel(self) -> QFrame:
        """创建场景面板"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame { 
                background: white; 
                border: 1px solid #e0e0e0; 
                border-radius: 6px; 
            }
        """)
        panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 标题栏
        header = QHBoxLayout()
        title = QLabel("场景列表")
        title.setFont(QFont("", 11, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("+ 添加")
        add_btn.setFixedHeight(26)
        add_btn.setStyleSheet("""
            QPushButton { 
                background: #0078d4; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover { background: #006cc1; }
        """)
        add_btn.clicked.connect(self.add_scene)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # 场景树
        self.scene_tree = QTreeWidget()
        self.scene_tree.setHeaderHidden(True)
        self.scene_tree.setStyleSheet("""
            QTreeWidget { 
                border: 1px solid #e0e0e0; 
                border-radius: 4px;
                background: white;
            }
            QTreeWidget::item { 
                padding: 6px; 
            }
            QTreeWidget::item:selected { 
                background: #0078d4; 
                color: white; 
            }
            QTreeWidget::item:hover {
                background: #f0f0f0;
            }
        """)
        self.scene_tree.itemClicked.connect(self.on_scene_clicked)
        self.scene_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scene_tree.customContextMenuRequested.connect(self.show_scene_menu)
        layout.addWidget(self.scene_tree)

        return panel

    def _create_action_panel(self) -> QFrame:
        """创建操作面板"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame { 
                background: white; 
                border: 1px solid #e0e0e0; 
                border-radius: 6px;
                margin-left: 5px;
                margin-right: 5px;
            }
        """)
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 标题栏
        header = QHBoxLayout()
        self.action_title = QLabel("操作列表")
        self.action_title.setFont(QFont("", 11, QFont.Bold))
        header.addWidget(self.action_title)
        header.addStretch()

        self.add_action_btn = QPushButton("+ 添加")
        self.add_action_btn.setFixedHeight(26)
        self.add_action_btn.setStyleSheet("""
            QPushButton { 
                background: #0078d4; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover { background: #006cc1; }
        """)
        self.add_action_btn.clicked.connect(self.add_action)
        self.add_action_btn.setEnabled(False)
        header.addWidget(self.add_action_btn)

        layout.addLayout(header)

        # 操作列表滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        self.action_widget = QWidget()
        self.action_widget.setStyleSheet("background: transparent;")
        self.action_layout = QVBoxLayout(self.action_widget)
        self.action_layout.setSpacing(5)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        self.action_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.action_widget)
        layout.addWidget(scroll)

        return panel

    def _create_preview_panel(self) -> QFrame:
        """创建预览面板"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame { 
                background: white; 
                border: 1px solid #e0e0e0; 
                border-radius: 6px; 
            }
        """)
        panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 窗口信息组
        window_group = QGroupBox("目标窗口")
        window_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        window_group.setFixedHeight(75)
        window_layout = QVBoxLayout(window_group)
        window_layout.setContentsMargins(8, 5, 8, 5)
        window_layout.setSpacing(5)

        self.window_info = QLabel("未连接")
        self.window_info.setStyleSheet("color: #666; font-size: 11px;")
        self.window_info.setWordWrap(True)
        window_layout.addWidget(self.window_info)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedHeight(26)
        self.refresh_btn.clicked.connect(self.refresh_window)
        btn_row.addWidget(self.refresh_btn)

        self.activate_btn = QPushButton("激活窗口")
        self.activate_btn.setFixedHeight(26)
        self.activate_btn.clicked.connect(self.activate_window)
        self.activate_btn.setEnabled(False)
        btn_row.addWidget(self.activate_btn)
        
        btn_row.addStretch()
        window_layout.addLayout(btn_row)

        layout.addWidget(window_group)

        # 预览组
        preview_group = QGroupBox("窗口预览")
        preview_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        preview_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(8, 10, 8, 8)
        preview_layout.setSpacing(8)

        # 预览容器
        self.preview_container = QFrame()
        self.preview_container.setStyleSheet("""
            QFrame {
                background: #1e1e1e;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        self.preview_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_container.setMinimumHeight(150)
        
        preview_container_layout = QVBoxLayout(self.preview_container)
        preview_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_label = QLabel("点击「开始预览」查看窗口")
        self.preview_label.setStyleSheet("color: #888; background: transparent; border: none;")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.mousePressEvent = self.on_preview_click
        preview_container_layout.addWidget(self.preview_label)
        
        preview_layout.addWidget(self.preview_container)

        # 预览控制按钮
        preview_btn_row = QHBoxLayout()
        preview_btn_row.setSpacing(8)
        
        self.preview_btn = QPushButton("开始预览")
        self.preview_btn.setFixedHeight(28)
        self.preview_btn.setCheckable(True)
        self.preview_btn.clicked.connect(self.toggle_preview)
        preview_btn_row.addWidget(self.preview_btn)

        self.pick_btn = QPushButton("🎯 拾取位置")
        self.pick_btn.setFixedHeight(28)
        self.pick_btn.setStyleSheet("""
            QPushButton { 
                background: #ff9800; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                padding: 4px 12px;
            }
            QPushButton:hover { background: #f57c00; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.pick_btn.clicked.connect(self.start_pick)
        self.pick_btn.setEnabled(False)
        preview_btn_row.addWidget(self.pick_btn)

        preview_layout.addLayout(preview_btn_row)
        layout.addWidget(preview_group)

        # 截图按钮
        self.capture_btn = QPushButton("📷 截取为场景识别图")
        self.capture_btn.setFixedHeight(32)
        self.capture_btn.clicked.connect(self.capture_scene)
        self.capture_btn.setEnabled(False)
        layout.addWidget(self.capture_btn)

        return panel

    def load_project(self, project_id: str):
        """加载项目"""
        self.current_project = self.project_manager.get_project(project_id)
        if not self.current_project:
            return

        self.title_label.setText(self.current_project.name)
        self.load_scenes()
        self.refresh_window()

        # 选择默认场景
        default = self.current_project.get_default_scene()
        if default:
            self.current_scene = default
            self.load_actions()

    def load_scenes(self):
        """加载场景列表"""
        self.scene_tree.clear()
        if not self.current_project:
            return

        for scene in self.current_project.scenes:
            text = scene.name
            if scene.is_default:
                text += " (默认)"
            if not scene.enabled:
                text += " [禁用]"
            text += f" ({len(scene.actions)})"

            item = QTreeWidgetItem([text])
            item.setData(0, Qt.UserRole, scene.id)
            if not scene.enabled:
                item.setForeground(0, Qt.gray)
            
            self.scene_tree.addTopLevelItem(item)

            if self.current_scene and scene.id == self.current_scene.id:
                self.scene_tree.setCurrentItem(item)

    def load_actions(self):
        """加载操作列表"""
        # 清除现有操作项
        for item in self.action_items:
            item.deleteLater()
        self.action_items.clear()

        # 清除布局中的弹性空间
        while self.action_layout.count():
            item = self.action_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.current_scene:
            self.action_title.setText("操作列表")
            self.add_action_btn.setEnabled(False)
            return

        self.action_title.setText(f"操作列表 - {self.current_scene.name}")
        self.add_action_btn.setEnabled(True)
        self.pick_btn.setEnabled(self.current_window is not None)
        self.capture_btn.setEnabled(self.current_window is not None)

        # 添加操作项
        sorted_actions = sorted(self.current_scene.actions, key=lambda a: a.order)
        for i, action in enumerate(sorted_actions):
            item = ActionItem(action, i)
            item.edit_clicked.connect(self.edit_action)
            item.delete_clicked.connect(self.delete_action)
            item.move_up_clicked.connect(lambda aid: self.move_action(aid, -1))
            item.move_down_clicked.connect(lambda aid: self.move_action(aid, 1))
            item.enabled_changed.connect(self.toggle_action)
                # 新增：长按排序菜单
            item.long_pressed.connect(self.on_action_long_pressed)

            self.action_layout.addWidget(item)
            self.action_items.append(item)

        # 添加弹性空间
        self.action_layout.addStretch()

    def on_scene_clicked(self, item):
        """场景点击"""
        scene_id = item.data(0, Qt.UserRole)
        if scene_id and self.current_project:
            self.current_scene = self.current_project.get_scene(scene_id)
            self.load_actions()

    def show_scene_menu(self, pos):
        item = self.scene_tree.itemAt(pos)
        if not item or not self.current_project:
            return

        scene_id = item.data(0, Qt.UserRole)
        scene = self.current_project.get_scene(scene_id)
        if not scene:
            return

        menu = QMenu(self)
        menu.addAction("✏️ 编辑").triggered.connect(lambda: self.edit_scene(scene_id))

        # 新增：上移/下移
        move_up_action = menu.addAction("⬆ 上移场景")
        move_down_action = menu.addAction("⬇ 下移场景")

        toggle_text = "🚫 禁用" if scene.enabled else "✅ 启用"
        menu.addAction(toggle_text).triggered.connect(lambda: self.toggle_scene(scene_id))

        if not scene.is_default:
            menu.addSeparator()
            menu.addAction("🗑️ 删除").triggered.connect(lambda: self.delete_scene(scene_id))

        chosen = menu.exec_(self.scene_tree.mapToGlobal(pos))
        if not chosen:
            return

        if chosen == move_up_action:
            self.current_project.move_scene(scene_id, -1)
        elif chosen == move_down_action:
            self.current_project.move_scene(scene_id, 1)

        # 保存并刷新
        self.project_manager.save_project(self.current_project)
        self.load_scenes()

    def add_scene(self):
        """添加场景"""
        if not self.current_project:
            return

        image_dir = self.project_manager.get_project_image_dir(self.current_project.id)
        hwnd = self.current_window.hwnd if self.current_window else None

        dialog = SceneDialog(self,
                            project=self.current_project,
                            hwnd=hwnd,
                            image_dir=image_dir)

        if dialog.exec_() == QDialog.Accepted:
            scene = dialog.get_scene()
            self.current_project.add_scene(scene)
            self.project_manager.save_project(self.current_project)
            self.load_scenes()

    def edit_scene(self, scene_id: str):
        if not self.current_project:
            return
        scene = self.current_project.get_scene(scene_id)
        if not scene:
            return

        image_dir = self.project_manager.get_project_image_dir(self.current_project.id)
        hwnd = self.current_window.hwnd if self.current_window else None

        dialog = SceneDialog(self,
                            scene=scene,
                            project=self.current_project,
                            hwnd=hwnd,
                            image_dir=image_dir)
        if dialog.exec_() == QDialog.Accepted:
            dialog.get_scene()  # scene 已是引用，直接被修改
            self.project_manager.save_project(self.current_project)
            self.load_scenes()

    def delete_scene(self, scene_id: str):
        """删除场景"""
        if not self.current_project:
            return
        scene = self.current_project.get_scene(scene_id)
        if not scene or scene.is_default:
            return
        if QMessageBox.question(self, "确认", f"删除场景「{scene.name}」？") == QMessageBox.Yes:
            self.current_project.remove_scene(scene_id)
            self.project_manager.save_project(self.current_project)
            if self.current_scene and self.current_scene.id == scene_id:
                self.current_scene = self.current_project.get_default_scene()
            self.load_scenes()
            self.load_actions()

    def toggle_scene(self, scene_id: str):
        """切换场景启用状态"""
        if not self.current_project:
            return
        scene = self.current_project.get_scene(scene_id)
        if scene:
            scene.enabled = not scene.enabled
            self.project_manager.save_project(self.current_project)
            self.load_scenes()

    def add_action(self):
        """添加操作"""
        if not self.current_scene:
            return
        dialog = ActionDialog(self)
        if dialog.exec_() == ActionDialog.Accepted:
            self.current_scene.add_action(dialog.get_action())
            self.project_manager.save_project(self.current_project)
            self.load_actions()
            self.load_scenes()

    def edit_action(self, action_id: str):
        """编辑操作"""
        if not self.current_scene:
            return
        action = self.current_scene.get_action(action_id)
        if not action:
            return
        dialog = ActionDialog(self, action=action)
        if dialog.exec_() == ActionDialog.Accepted:
            dialog.get_action()
            self.project_manager.save_project(self.current_project)
            self.load_actions()

    def delete_action(self, action_id: str):
        """删除操作"""
        if not self.current_scene:
            return
        if QMessageBox.question(self, "确认", "删除此操作？") == QMessageBox.Yes:
            self.current_scene.remove_action(action_id)
            self.project_manager.save_project(self.current_project)
            self.load_actions()
            self.load_scenes()

    def move_action(self, action_id: str, direction: int):
        """移动操作"""
        if not self.current_scene:
            return
        self.current_scene.move_action(action_id, direction)
        self.project_manager.save_project(self.current_project)
        self.load_actions()

    def toggle_action(self, action_id: str, enabled: bool):
        """切换操作启用状态"""
        if not self.current_scene:
            return
        action = self.current_scene.get_action(action_id)
        if action:
            action.enabled = enabled
            self.project_manager.save_project(self.current_project)

    def refresh_window(self):
        """刷新目标窗口"""
        if not self.current_project or not self.current_project.target_window_title:
            self.current_window = None
            self.window_info.setText("未设置目标窗口")
            self.window_info.setStyleSheet("color: #666; font-size: 11px;")
            self.activate_btn.setEnabled(False)
            self.pick_btn.setEnabled(False)
            self.capture_btn.setEnabled(False)
            return

        window = self.window_manager.find_window_by_title(self.current_project.target_window_title)
        if window:
            self.current_window = window
            title = window.title[:30] + "..." if len(window.title) > 30 else window.title
            self.window_info.setText(f"✓ {title}")
            self.window_info.setStyleSheet("color: #28a745; font-size: 11px;")
            self.activate_btn.setEnabled(True)
            self.pick_btn.setEnabled(self.current_scene is not None)
            self.capture_btn.setEnabled(self.current_scene is not None)
        else:
            self.current_window = None
            target = self.current_project.target_window_title
            self.window_info.setText(f"✗ 未找到: {target[:20]}...")
            self.window_info.setStyleSheet("color: #dc3545; font-size: 11px;")
            self.activate_btn.setEnabled(False)
            self.pick_btn.setEnabled(False)
            self.capture_btn.setEnabled(False)

    def activate_window(self):
        """激活窗口"""
        if self.current_window:
            import win32gui
            import win32con
            try:
                if win32gui.IsIconic(self.current_window.hwnd):
                    win32gui.ShowWindow(self.current_window.hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(self.current_window.hwnd)
            except Exception as e:
                print(f"激活窗口失败: {e}")

    def toggle_preview(self, checked: bool):
        """切换预览"""
        if checked:
            self.preview_btn.setText("停止预览")
            self.preview_timer.start(300)
        else:
            self.preview_btn.setText("开始预览")
            self.preview_timer.stop()
            self.preview_label.setText("点击「开始预览」查看窗口")
            self.preview_label.setPixmap(QPixmap())
            self._preview_pixmap = None

    def update_preview(self):
        """更新预览"""
        if not self.current_window:
            self.preview_label.setText("未连接窗口")
            return
            
        if not self.window_manager.is_window_valid(self.current_window.hwnd):
            self.preview_label.setText("窗口已关闭")
            self.current_window = None
            return

        image = self.window_manager.capture_window(self.current_window.hwnd)
        if image:
            image = image.convert("RGB")
            data = image.tobytes("raw", "RGB")
            qimage = QImage(data, image.width, image.height, QImage.Format_RGB888)
            self._preview_pixmap = QPixmap.fromImage(qimage)
            self._update_preview_display()

    def _update_preview_display(self):
        """更新预览显示"""
        if not self._preview_pixmap:
            return
            
        container_size = self.preview_container.size()
        available_width = container_size.width() - 4
        available_height = container_size.height() - 4
        
        if available_width <= 0 or available_height <= 0:
            return
        
        scaled = self._preview_pixmap.scaled(
            available_width, 
            available_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled)

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        if self._preview_pixmap:
            self._update_preview_display()

    def start_pick(self):
        """开始拾取位置"""
        if not self.current_window or not self.current_scene:
            return
        if not self.preview_timer.isActive():
            self.preview_btn.setChecked(True)
            self.toggle_preview(True)
        self._picking_position = True
        self.pick_btn.setText("点击预览选择...")
        self.preview_label.setCursor(Qt.CrossCursor)

    def on_preview_click(self, event):
        """预览点击"""
        if not self._picking_position:
            return
        if not self.current_window or not self.current_scene:
            return

        pixmap = self.preview_label.pixmap()
        if not pixmap or pixmap.isNull():
            return

        label_size = self.preview_label.size()
        pixmap_size = pixmap.size()
        
        x_offset = (label_size.width() - pixmap_size.width()) // 2
        y_offset = (label_size.height() - pixmap_size.height()) // 2

        click_x = event.pos().x() - x_offset
        click_y = event.pos().y() - y_offset

        if click_x < 0 or click_y < 0 or click_x > pixmap_size.width() or click_y > pixmap_size.height():
            return

        relative_x = click_x / pixmap_size.width()
        relative_y = click_y / pixmap_size.height()

        self._picking_position = False
        self.pick_btn.setText("🎯 拾取位置")
        self.preview_label.setCursor(Qt.ArrowCursor)

        action = Action(
            name=f"点击 ({relative_x:.2f}, {relative_y:.2f})",
            relative_x=relative_x,
            relative_y=relative_y
        )

        dialog = ActionDialog(self, action=action)
        if dialog.exec_() == ActionDialog.Accepted:
            self.current_scene.add_action(dialog.get_action())
            self.project_manager.save_project(self.current_project)
            self.load_actions()
            self.load_scenes()

    def capture_scene(self):
        """截取场景图"""
        if not self.current_window or not self.current_scene or not self.current_project:
            return
        image_dir = self.project_manager.get_project_image_dir(self.current_project.id)
        path = f"{image_dir}/scene_{self.current_scene.id}.png"
        if self.scene_manager.capture_scene_image(self.current_window.hwnd, path):
            self.current_scene.recognition_image_path = path
            self.project_manager.save_project(self.current_project)
            QMessageBox.information(self, "成功", "已保存场景识别图片")
        else:
            QMessageBox.warning(self, "失败", "截图失败")

    def edit_settings(self):
        """编辑项目设置"""
        if not self.current_project:
            return
        dialog = ProjectDialog(self, project=self.current_project, 
                               groups=self.project_manager.get_groups())
        if dialog.exec_() == ProjectDialog.Accepted:
            dialog.get_project()
            self.project_manager.save_project(self.current_project)
            self.title_label.setText(self.current_project.name)
            self.refresh_window()

    def on_back(self):
        """返回"""
        if self.preview_timer.isActive():
            self.preview_timer.stop()
        self._preview_pixmap = None
        self.back_clicked.emit()

    def on_run(self):
        """运行"""
        if self.current_project:
            self.run_clicked.emit(self.current_project.id)

    def save_current(self):
        """保存当前项目"""
        if self.current_project:
            self.project_manager.save_project(self.current_project)

    def on_action_long_pressed(self, action_id: str):
        """长按操作项，弹出上移/下移菜单"""
        if not self.current_scene:
            return

        menu = QMenu(self)
        up_action = menu.addAction("⬆ 上移操作")
        down_action = menu.addAction("⬇ 下移操作")

        chosen = menu.exec_(QCursor.pos())
        if not chosen:
            return

        if chosen == up_action:
            self.current_scene.move_action(action_id, -1)
        elif chosen == down_action:
            self.current_scene.move_action(action_id, 1)

        self.project_manager.save_project(self.current_project)
        self.load_actions()
        self.load_scenes()