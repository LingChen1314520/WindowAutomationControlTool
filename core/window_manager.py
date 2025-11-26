"""窗口管理模块"""
import win32gui
import win32con
import win32ui
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from typing import List, Optional, Tuple
from PIL import Image


@dataclass
class WindowInfo:
    """窗口信息"""
    hwnd: int
    title: str
    class_name: str
    rect: Tuple[int, int, int, int]
    is_visible: bool
    is_minimized: bool

    @property
    def width(self) -> int:
        return self.rect[2] - self.rect[0]

    @property
    def height(self) -> int:
        return self.rect[3] - self.rect[1]

    @property
    def client_width(self) -> int:
        """客户区宽度"""
        try:
            rect = win32gui.GetClientRect(self.hwnd)
            return rect[2] - rect[0]
        except:
            return self.width

    @property
    def client_height(self) -> int:
        """客户区高度"""
        try:
            rect = win32gui.GetClientRect(self.hwnd)
            return rect[3] - rect[1]
        except:
            return self.height


class WindowManager:
    """窗口管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._windows = []
        return cls._instance

    def refresh_windows(self) -> List[WindowInfo]:
        """刷新并获取所有窗口"""
        self._windows = []

        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    class_name = win32gui.GetClassName(hwnd)
                    rect = win32gui.GetWindowRect(hwnd)
                    is_minimized = win32gui.IsIconic(hwnd)
                    
                    window_info = WindowInfo(
                        hwnd=hwnd,
                        title=title,
                        class_name=class_name,
                        rect=rect,
                        is_visible=True,
                        is_minimized=bool(is_minimized)
                    )
                    self._windows.append(window_info)
            return True

        win32gui.EnumWindows(enum_callback, None)
        return self._windows

    def get_windows(self) -> List[WindowInfo]:
        return self._windows

    def find_window_by_title(self, title: str, partial: bool = True) -> Optional[WindowInfo]:
        """通过标题查找窗口"""
        self.refresh_windows()
        for window in self._windows:
            if partial:
                if title.lower() in window.title.lower():
                    return window
            else:
                if title == window.title:
                    return window
        return None

    def find_window_by_hwnd(self, hwnd: int) -> Optional[WindowInfo]:
        """通过句柄查找窗口"""
        try:
            if win32gui.IsWindow(hwnd):
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                is_minimized = win32gui.IsIconic(hwnd)
                is_visible = win32gui.IsWindowVisible(hwnd)
                
                return WindowInfo(
                    hwnd=hwnd,
                    title=title,
                    class_name=class_name,
                    rect=rect,
                    is_visible=is_visible,
                    is_minimized=bool(is_minimized)
                )
        except:
            pass
        return None

    @staticmethod
    def get_client_rect(hwnd: int) -> Tuple[int, int, int, int]:
        """获取客户区矩形"""
        try:
            rect = win32gui.GetClientRect(hwnd)
            return rect
        except:
            return (0, 0, 0, 0)

    @staticmethod
    def capture_window(hwnd: int) -> Optional[Image.Image]:
        """截取窗口图像（后台截图）"""
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                return None

            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)

            # 使用 PrintWindow 进行后台截图
            ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)

            bmpinfo = bitmap.GetInfo()
            bmpstr = bitmap.GetBitmapBits(True)
            
            image = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )

            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)

            return image

        except Exception as e:
            print(f"截取窗口失败: {e}")
            return None

    @staticmethod
    def is_window_valid(hwnd: int) -> bool:
        """检查窗口是否有效"""
        try:
            return bool(win32gui.IsWindow(hwnd))
        except:
            return False