"""执行管理器 - 管理多个项目的并行执行"""
import time
from typing import Dict, Optional, Callable, List
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from models import Project, Scene
from .window_manager import WindowManager
from .scene_manager import SceneManager
from .background_executor import BackgroundExecutor


class ProjectExecutionWorker(QThread):
    """项目执行工作线程"""
    
    # 信号定义
    log_signal = pyqtSignal(str, str)  # project_id, message
    scene_changed = pyqtSignal(str, str)  # project_id, scene_name
    action_executed = pyqtSignal(str, str)  # project_id, action_name
    progress_signal = pyqtSignal(str, int, int)  # project_id, current, total
    status_changed = pyqtSignal(str, str)  # project_id, status
    finished_signal = pyqtSignal(str, bool, str)  # project_id, success, message

    def __init__(self, project: Project, hwnd: int):
        super().__init__()
        self.project = project
        self.hwnd = hwnd
        self.project_id = project.id
        
        self.window_manager = WindowManager()
        self.scene_manager = SceneManager()
        self.executor = BackgroundExecutor()
        
        self._stop_flag = False
        self._pause_flag = False

    def run(self):
        """执行项目"""
        try:
            self.status_changed.emit(self.project_id, "running")
            loop_count = 0
            max_loops = self.project.max_loop_count if self.project.loop_execution else 1

            while not self._stop_flag:
                loop_count += 1
                self.log_signal.emit(self.project_id, f"=== 开始第 {loop_count} 轮执行 ===")

                # 检查窗口
                if not self.window_manager.is_window_valid(self.hwnd):
                    self.finished_signal.emit(self.project_id, False, "目标窗口已关闭")
                    return

                # 识别或获取场景
                scene = self._get_current_scene()
                if not scene:
                    self.finished_signal.emit(self.project_id, False, "没有可执行的场景")
                    return

                self.scene_changed.emit(self.project_id, scene.name)
                self.log_signal.emit(self.project_id, f"当前场景: {scene.name}")

                # 执行场景
                success = self._execute_scene(scene)
                
                if not success and self._stop_flag:
                    self.finished_signal.emit(self.project_id, False, "已停止")
                    return

                # 检查循环
                if not self.project.loop_execution:
                    break

                if max_loops > 0 and loop_count >= max_loops:
                    self.log_signal.emit(self.project_id, f"已达到最大循环次数: {max_loops}")
                    break

                # 循环间隔
                self._wait_with_check(self.project.recognize_interval / 1000)

            self.finished_signal.emit(self.project_id, True, "执行完成")

        except Exception as e:
            self.finished_signal.emit(self.project_id, False, f"执行错误: {str(e)}")
        finally:
            self.status_changed.emit(self.project_id, "stopped")

    def _get_current_scene(self) -> Optional[Scene]:
        """获取当前场景"""
        if self.project.auto_recognize_scene:
            scene = self.scene_manager.recognize_scene(
                self.hwnd,
                self.project.get_enabled_scenes()
            )
            if scene:
                return scene
        
        return self.project.get_default_scene()

    def _execute_scene(self, scene: Scene) -> bool:
        """执行场景中的操作"""
        actions = scene.get_enabled_actions()
        total = len(actions)

        for i, action in enumerate(actions):
            if self._stop_flag:
                return False

            while self._pause_flag:
                time.sleep(0.1)
                if self._stop_flag:
                    return False

            self.progress_signal.emit(self.project_id, i + 1, total)
            self.action_executed.emit(self.project_id, action.name)

            def log_callback(msg):
                self.log_signal.emit(self.project_id, msg)

            success = self.executor.execute_action(action, self.hwnd, log_callback)
            
            if not success:
                self.log_signal.emit(self.project_id, f"操作失败: {action.name}")

        return True

    def _wait_with_check(self, seconds: float):
        """等待并检查停止标志"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            if self._stop_flag:
                break
            time.sleep(0.1)

    def stop(self):
        """停止执行"""
        self._stop_flag = True
        self.executor.stop()

    def pause(self):
        """暂停执行"""
        self._pause_flag = True
        self.executor.pause()
        self.status_changed.emit(self.project_id, "paused")

    def resume(self):
        """恢复执行"""
        self._pause_flag = False
        self.executor.resume()
        self.status_changed.emit(self.project_id, "running")

    def is_running(self) -> bool:
        return self.isRunning() and not self._stop_flag

    def is_paused(self) -> bool:
        return self._pause_flag


class ExecutionManager(QObject):
    """执行管理器 - 管理多个项目的并行执行"""
    
    # 汇总信号
    project_started = pyqtSignal(str)  # project_id
    project_stopped = pyqtSignal(str)  # project_id
    project_log = pyqtSignal(str, str)  # project_id, message
    project_progress = pyqtSignal(str, int, int)  # project_id, current, total
    project_status = pyqtSignal(str, str)  # project_id, status
    project_finished = pyqtSignal(str, bool, str)  # project_id, success, message

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._workers: Dict[str, ProjectExecutionWorker] = {}
        self.window_manager = WindowManager()

    def start_project(self, project: Project) -> tuple:
        """启动项目执行"""
        # 检查是否已在运行
        if project.id in self._workers:
            worker = self._workers[project.id]
            if worker.isRunning():
                return False, "项目已在运行中"

        # 查找目标窗口
        window = self.window_manager.find_window_by_title(project.target_window_title)
        if not window:
            return False, f"未找到目标窗口: {project.target_window_title}"

        # 创建工作线程
        worker = ProjectExecutionWorker(project, window.hwnd)
        
        # 连接信号
        worker.log_signal.connect(self.project_log.emit)
        worker.progress_signal.connect(self.project_progress.emit)
        worker.status_changed.connect(self.project_status.emit)
        worker.finished_signal.connect(self._on_worker_finished)
        worker.scene_changed.connect(lambda pid, s: self.project_log.emit(pid, f"场景: {s}"))
        worker.action_executed.connect(lambda pid, a: self.project_log.emit(pid, f"操作: {a}"))

        self._workers[project.id] = worker
        worker.start()
        
        self.project_started.emit(project.id)
        return True, "已启动"

    def stop_project(self, project_id: str):
        """停止项目执行"""
        if project_id in self._workers:
            worker = self._workers[project_id]
            if worker.isRunning():
                worker.stop()
                worker.wait(3000)  # 等待最多3秒
                if worker.isRunning():
                    worker.terminate()
            self.project_stopped.emit(project_id)

    def pause_project(self, project_id: str):
        """暂停项目执行"""
        if project_id in self._workers:
            self._workers[project_id].pause()

    def resume_project(self, project_id: str):
        """恢复项目执行"""
        if project_id in self._workers:
            self._workers[project_id].resume()

    def stop_all(self):
        """停止所有项目"""
        for project_id in list(self._workers.keys()):
            self.stop_project(project_id)

    def is_running(self, project_id: str) -> bool:
        """检查项目是否正在运行"""
        if project_id in self._workers:
            return self._workers[project_id].is_running()
        return False

    def is_paused(self, project_id: str) -> bool:
        """检查项目是否暂停"""
        if project_id in self._workers:
            return self._workers[project_id].is_paused()
        return False

    def get_running_projects(self) -> List[str]:
        """获取正在运行的项目ID列表"""
        return [pid for pid, worker in self._workers.items() if worker.is_running()]

    def _on_worker_finished(self, project_id: str, success: bool, message: str):
        """工作线程完成回调"""
        self.project_finished.emit(project_id, success, message)
        if project_id in self._workers:
            self._workers[project_id].deleteLater()
            del self._workers[project_id]