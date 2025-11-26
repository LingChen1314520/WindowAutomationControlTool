"""窗口自动化控制软件 - 后台执行版"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from ui import MainWindow


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

      # 图标路径（支持以后打包）
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "ico_256x256.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))   # 设置应用全局图标

    app.setStyleSheet("""
        * { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; }
        QToolTip {
            background: #333; color: white;
            border: 1px solid #555; padding: 5px; border-radius: 3px;
        }
        QScrollBar:vertical {
            border: none; background: #f0f0f0; width: 8px; border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: #c0c0c0; border-radius: 4px; min-height: 20px;
        }
        QScrollBar::handle:vertical:hover { background: #a0a0a0; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal {
            border: none; background: #f0f0f0; height: 8px; border-radius: 4px;
        }
        QScrollBar::handle:horizontal {
            background: #c0c0c0; border-radius: 4px; min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover { background: #a0a0a0; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-top: 8px;
            padding-top: 8px;
            background: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #333;
        }
    """)

    window = MainWindow()
        # 再给主窗口单独设置一次，避免某些环境下不生效
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()