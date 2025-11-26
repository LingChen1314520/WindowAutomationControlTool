"""场景管理器"""
import cv2
import numpy as np
from PIL import Image
from typing import Optional, List
import os
from models import Scene
from .window_manager import WindowManager


class SceneManager:
    """场景管理器"""

    def __init__(self):
        self.window_manager = WindowManager()

    def capture_scene_image(self, hwnd: int, save_path: str) -> bool:
        """捕获场景图像并保存"""
        try:
            image = self.window_manager.capture_window(hwnd)
            if image:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                image.save(save_path)
                return True
            return False
        except Exception as e:
            print(f"捕获场景图像失败: {e}")
            return False

    def recognize_scene(self, hwnd: int, scenes: List[Scene]) -> Optional[Scene]:
        """基于锚点（anchor）的局部模板匹配，优先识别场景"""
        try:
            current_image = self.window_manager.capture_window(hwnd)
            if not current_image:
                return None

            current_cv = cv2.cvtColor(np.array(current_image), cv2.COLOR_RGB2BGR)
            h, w = current_cv.shape[:2]

            best_scene = None
            best_score = 0.0

            for scene in scenes:
                if not scene.enabled:
                    continue

                scene_best = 0.0
                matched_by_anchor = False

                # ---------- 1. 优先使用 anchors ----------
                if getattr(scene, "anchors", None):
                    for anchor in scene.anchors:
                        if not anchor.image_path or not os.path.exists(anchor.image_path):
                            continue

                        # 读取 anchor 模板（支持中文路径）
                        try:
                            tmpl = cv2.imdecode(
                                np.fromfile(anchor.image_path, dtype=np.uint8),
                                cv2.IMREAD_COLOR
                            )
                        except Exception as e:
                            print(f"读取锚点图片失败: {anchor.image_path} {e}")
                            continue

                        if tmpl is None:
                            continue

                        th, tw = tmpl.shape[:2]

                        # 计算 ROI 像素区域
                        x1 = int(w * anchor.roi_x)
                        y1 = int(h * anchor.roi_y)
                        x2 = int(w * (anchor.roi_x + anchor.roi_w))
                        y2 = int(h * (anchor.roi_y + anchor.roi_h))

                        # 边界保护
                        x1 = max(0, min(x1, w - 1))
                        y1 = max(0, min(y1, h - 1))
                        x2 = max(x1 + 1, min(x2, w))
                        y2 = max(y1 + 1, min(y2, h))

                        roi = current_cv[y1:y2, x1:x2]
                        rh, rw = roi.shape[:2]

                        if rh < th or rw < tw:
                            # ROI 比模板小，跳过这个 anchor
                            continue

                        # 模板匹配
                        res = cv2.matchTemplate(roi, tmpl, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(res)

                        if max_val > scene_best:
                            scene_best = max_val

                        # 如果单个锚点达到自己的阈值，就认为该场景被 anchors 匹配到了
                        if max_val >= anchor.threshold:
                            matched_by_anchor = True

                    if matched_by_anchor:
                        # 这个场景被 anchors 命中，使用 anchors 得到的最高分参与全局比较
                        if scene_best > best_score:
                            best_score = scene_best
                            best_scene = scene
                        # 已经用 anchors 决定该场景，不再用整图兜底
                        continue

                # ---------- 2. 回退：使用整图模板匹配 ----------
                if scene.recognition_image_path and os.path.exists(scene.recognition_image_path):
                    try:
                        template = cv2.imdecode(
                            np.fromfile(scene.recognition_image_path, dtype=np.uint8),
                            cv2.IMREAD_COLOR
                        )
                    except Exception as e:
                        print(f"读取场景整图失败: {scene.recognition_image_path} {e}")
                        template = None

                    if template is not None:
                        score = self._match_images(current_cv, template)
                        if score > scene.recognition_threshold and score > best_score:
                            best_score = score
                            best_scene = scene

            # 没有任何场景匹配，则返回默认场景
            if best_scene is None:
                for scene in scenes:
                    if scene.is_default and scene.enabled:
                        return scene

            return best_scene

        except Exception as e:
            print(f"场景识别失败: {e}")
            return None

    def _match_images(self, image1: np.ndarray, image2: np.ndarray) -> float:
        """比较两张图片的相似度（整图匹配兜底）"""
        try:
            h1, w1 = image1.shape[:2]
            h2, w2 = image2.shape[:2]

            target_h = min(h1, h2, 480)
            target_w = min(w1, w2, 640)

            if target_h <= 0 or target_w <= 0:
                return 0.0

            img1_resized = cv2.resize(image1, (target_w, target_h))
            img2_resized = cv2.resize(image2, (target_w, target_h))

            gray1 = cv2.cvtColor(img1_resized, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2_resized, cv2.COLOR_BGR2GRAY)

            result = cv2.matchTemplate(gray1, gray2, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)

            return max_val

        except Exception as e:
            print(f"图像匹配失败: {e}")
            return 0.0