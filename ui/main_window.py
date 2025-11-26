"""主窗口"""
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QDesktopWidget
from PyQt5.QtCore import Qt
from core import ExecutionManager
from .home_page import HomePage
from .project_page import ProjectPage


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.execution_manager = ExecutionManager()
        self.setup_ui()
        self.center_window()

    def setup_ui(self):
        self.setWindowTitle("零界点")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)
        self.setStyleSheet("QMainWindow { background: #f5f5f5; }")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home_page = HomePage()
        self.home_page.project_selected.connect(self.open_project)

        self.project_page = ProjectPage()
        self.project_page.back_clicked.connect(self.show_home)
        self.project_page.run_clicked.connect(self.run_project)

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.project_page)

        self.stack.setCurrentWidget(self.home_page)

    def center_window(self):
        """窗口居中显示"""
        screen = QDesktopWidget().availableGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def show_home(self):
        """显示主页"""
        self.home_page.refresh()
        self.stack.setCurrentWidget(self.home_page)

    def open_project(self, project_id: str):
        """打开项目"""
        self.project_page.load_project(project_id)
        self.stack.setCurrentWidget(self.project_page)

    def run_project(self, project_id: str):
        """运行项目"""
        self.home_page.run_project(project_id)
        self.stack.setCurrentWidget(self.home_page)

    def closeEvent(self, event):
        """关闭事件"""
        self.execution_manager.stop_all()
        if self.project_page.current_project:
            self.project_page.save_current()
        event.accept()