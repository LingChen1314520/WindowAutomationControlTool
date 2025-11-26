"""后台执行器 - 使用Windows消息实现后台操作，不影响用户鼠标键盘"""
import time
import ctypes
from ctypes import wintypes
import win32gui
import win32con
import win32api
from typing import Optional, Callable
from models import Action, ActionType
from .window_manager import WindowManager, WindowInfo


# Windows API 常量
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MOUSEMOVE = 0x0200
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
WM_SETTEXT = 0x000C

MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002


def MAKELPARAM(low, high):
    """创建 LPARAM"""
    return (high << 16) | (low & 0xFFFF)


class BackgroundExecutor:
    """后台执行器 - 在指定窗口后台执行操作，不影响用户操作"""

    def __init__(self):
        self.window_manager = WindowManager()
        self._stop_flag = False
        self._pause_flag = False

    def stop(self):
        self._stop_flag = True

    def pause(self):
        self._pause_flag = True

    def resume(self):
        self._pause_flag = False

    def reset(self):
        self._stop_flag = False
        self._pause_flag = False

    def is_stopped(self) -> bool:
        return self._stop_flag

    def is_paused(self) -> bool:
        return self._pause_flag

    def execute_action(self, action: Action, hwnd: int,
                       callback: Optional[Callable] = None) -> bool:
        """在指定窗口后台执行操作"""
        if self._stop_flag:
            return False

        while self._pause_flag:
            time.sleep(0.1)
            if self._stop_flag:
                return False

        try:
            # 检查窗口是否有效
            if not win32gui.IsWindow(hwnd):
                if callback:
                    callback(f"窗口无效: {hwnd}")
                return False

            # 获取窗口客户区大小
            client_rect = win32gui.GetClientRect(hwnd)
            width = client_rect[2]
            height = client_rect[3]

            if width <= 0 or height <= 0:
                if callback:
                    callback("窗口大小无效")
                return False

            # 计算点击坐标（相对于客户区）
            x = int(width * action.relative_x)
            y = int(height * action.relative_y)

            if callback:
                callback(f"执行: {action.name}")

            success = False
            
            if action.action_type == ActionType.CLICK:
                success = self._background_click(hwnd, x, y)
            elif action.action_type == ActionType.DOUBLE_CLICK:
                success = self._background_double_click(hwnd, x, y)
            elif action.action_type == ActionType.RIGHT_CLICK:
                success = self._background_right_click(hwnd, x, y)
            elif action.action_type == ActionType.DRAG:
                end_x = int(width * action.end_relative_x)
                end_y = int(height * action.end_relative_y)
                success = self._background_drag(hwnd, x, y, end_x, end_y)
            elif action.action_type == ActionType.KEY_PRESS:
                success = self._background_key_press(hwnd, action.key)
            elif action.action_type == ActionType.INPUT_TEXT:
                success = self._background_input_text(hwnd, action.text)
            elif action.action_type == ActionType.WAIT:
                success = self._wait(action.wait_time)

            # 操作后延迟
            if success and action.delay_after > 0:
                time.sleep(action.delay_after / 1000)

            return success

        except Exception as e:
            if callback:
                callback(f"执行失败: {e}")
            return False

    def _background_click(self, hwnd: int, x: int, y: int) -> bool:
        """后台单击"""
        try:
            lparam = MAKELPARAM(x, y)
            
            # 发送鼠标按下和释放消息
            win32gui.PostMessage(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
            time.sleep(0.05)
            win32gui.PostMessage(hwnd, WM_LBUTTONUP, 0, lparam)
            
            return True
        except Exception as e:
            print(f"后台点击失败: {e}")
            return False

    def _background_double_click(self, hwnd: int, x: int, y: int) -> bool:
        """后台双击"""
        try:
            lparam = MAKELPARAM(x, y)
            
            # 发送双击消息
            win32gui.PostMessage(hwnd, WM_LBUTTONDBLCLK, MK_LBUTTON, lparam)
            time.sleep(0.05)
            win32gui.PostMessage(hwnd, WM_LBUTTONUP, 0, lparam)
            
            return True
        except Exception as e:
            print(f"后台双击失败: {e}")
            return False

    def _background_right_click(self, hwnd: int, x: int, y: int) -> bool:
        """后台右键单击"""
        try:
            lparam = MAKELPARAM(x, y)
            
            win32gui.PostMessage(hwnd, WM_RBUTTONDOWN, MK_RBUTTON, lparam)
            time.sleep(0.05)
            win32gui.PostMessage(hwnd, WM_RBUTTONUP, 0, lparam)
            
            return True
        except Exception as e:
            print(f"后台右键点击失败: {e}")
            return False

    def _background_drag(self, hwnd: int, start_x: int, start_y: int,
                         end_x: int, end_y: int) -> bool:
        """后台拖拽"""
        try:
            # 按下鼠标
            lparam = MAKELPARAM(start_x, start_y)
            win32gui.PostMessage(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
            time.sleep(0.05)
            
            # 移动鼠标
            steps = 20
            for i in range(steps + 1):
                if self._stop_flag:
                    break
                current_x = int(start_x + (end_x - start_x) * i / steps)
                current_y = int(start_y + (end_y - start_y) * i / steps)
                lparam = MAKELPARAM(current_x, current_y)
                win32gui.PostMessage(hwnd, WM_MOUSEMOVE, MK_LBUTTON, lparam)
                time.sleep(0.02)
            
            # 释放鼠标
            lparam = MAKELPARAM(end_x, end_y)
            win32gui.PostMessage(hwnd, WM_LBUTTONUP, 0, lparam)
            
            return True
        except Exception as e:
            print(f"后台拖拽失败: {e}")
            return False

    def _background_key_press(self, hwnd: int, key: str) -> bool:
        """后台按键"""
        try:
            key_map = {
                'enter': win32con.VK_RETURN,
                'tab': win32con.VK_TAB,
                'escape': win32con.VK_ESCAPE,
                'esc': win32con.VK_ESCAPE,
                'space': win32con.VK_SPACE,
                'backspace': win32con.VK_BACK,
                'delete': win32con.VK_DELETE,
                'up': win32con.VK_UP,
                'down': win32con.VK_DOWN,
                'left': win32con.VK_LEFT,
                'right': win32con.VK_RIGHT,
                'home': win32con.VK_HOME,
                'end': win32con.VK_END,
                'pageup': win32con.VK_PRIOR,
                'pagedown': win32con.VK_NEXT,
                'f1': win32con.VK_F1,
                'f2': win32con.VK_F2,
                'f3': win32con.VK_F3,
                'f4': win32con.VK_F4,
                'f5': win32con.VK_F5,
                'f6': win32con.VK_F6,
                'f7': win32con.VK_F7,
                'f8': win32con.VK_F8,
                'f9': win32con.VK_F9,
                'f10': win32con.VK_F10,
                'f11': win32con.VK_F11,
                'f12': win32con.VK_F12,
                'ctrl': win32con.VK_CONTROL,
                'alt': win32con.VK_MENU,
                'shift': win32con.VK_SHIFT,
            }

            key_lower = key.lower().strip()
            
            # 处理组合键
            if '+' in key_lower:
                return self._background_combo_key(hwnd, key_lower, key_map)
            
            # 单个按键
            if key_lower in key_map:
                vk_code = key_map[key_lower]
            elif len(key) == 1:
                vk_code = ord(key.upper())
            else:
                return False

            # 发送按键消息
            scan_code = win32api.MapVirtualKey(vk_code, 0)
            lparam_down = (scan_code << 16) | 1
            lparam_up = (scan_code << 16) | 0xC0000001

            win32gui.PostMessage(hwnd, WM_KEYDOWN, vk_code, lparam_down)
            time.sleep(0.05)
            win32gui.PostMessage(hwnd, WM_KEYUP, vk_code, lparam_up)

            return True
        except Exception as e:
            print(f"后台按键失败: {e}")
            return False

    def _background_combo_key(self, hwnd: int, key_str: str, key_map: dict) -> bool:
        """后台组合键"""
        try:
            parts = [p.strip() for p in key_str.split('+')]
            modifiers = []
            main_key = None

            for part in parts:
                if part in ['ctrl', 'alt', 'shift']:
                    modifiers.append(key_map[part])
                else:
                    main_key = part

            # 按下修饰键
            for mod in modifiers:
                scan_code = win32api.MapVirtualKey(mod, 0)
                lparam = (scan_code << 16) | 1
                win32gui.PostMessage(hwnd, WM_KEYDOWN, mod, lparam)
                time.sleep(0.02)

            # 按下主键
            if main_key:
                if main_key in key_map:
                    vk_code = key_map[main_key]
                elif len(main_key) == 1:
                    vk_code = ord(main_key.upper())
                else:
                    vk_code = None

                if vk_code:
                    scan_code = win32api.MapVirtualKey(vk_code, 0)
                    lparam_down = (scan_code << 16) | 1
                    lparam_up = (scan_code << 16) | 0xC0000001
                    
                    win32gui.PostMessage(hwnd, WM_KEYDOWN, vk_code, lparam_down)
                    time.sleep(0.05)
                    win32gui.PostMessage(hwnd, WM_KEYUP, vk_code, lparam_up)

            # 释放修饰键
            for mod in reversed(modifiers):
                scan_code = win32api.MapVirtualKey(mod, 0)
                lparam = (scan_code << 16) | 0xC0000001
                win32gui.PostMessage(hwnd, WM_KEYUP, mod, lparam)
                time.sleep(0.02)

            return True
        except Exception as e:
            print(f"后台组合键失败: {e}")
            return False

    def _background_input_text(self, hwnd: int, text: str) -> bool:
        """后台输入文本"""
        try:
            for char in text:
                # 使用 WM_CHAR 发送字符
                win32gui.PostMessage(hwnd, WM_CHAR, ord(char), 0)
                time.sleep(0.02)
            return True
        except Exception as e:
            print(f"后台输入文本失败: {e}")
            return False

    def _wait(self, milliseconds: int) -> bool:
        """等待"""
        start_time = time.time()
        while (time.time() - start_time) * 1000 < milliseconds:
            if self._stop_flag:
                return False
            time.sleep(0.1)
        return True

    def find_child_at_point(self, hwnd: int, x: int, y: int) -> int:
        """查找指定位置的子窗口"""
        try:
            # 转换为屏幕坐标
            rect = win32gui.GetWindowRect(hwnd)
            screen_x = rect[0] + x
            screen_y = rect[1] + y
            
            # 查找该位置的窗口
            child = win32gui.WindowFromPoint((screen_x, screen_y))
            
            # 确保是目标窗口的子窗口
            if child and (child == hwnd or win32gui.IsChild(hwnd, child)):
                return child
            
            return hwnd
        except:
            return hwnd