"""场景模型"""
from dataclasses import dataclass, field
from typing import List, Optional
import uuid
from .action import Action
from dataclasses import dataclass, field
from typing import List, Optional
import uuid
from .action import Action


@dataclass
class SceneAnchor:
    """场景识别锚点：某个特定按钮/图标的小图"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    image_path: str = ""        # 小模板图片路径
    threshold: float = 0.85     # 该锚点自己的阈值（0~1）
    # 预期出现区域（相对窗口客户区 0~1）
    roi_x: float = 0.0          # 左上角 x
    roi_y: float = 0.0          # 左上角 y
    roi_w: float = 1.0          # 宽度比例
    roi_h: float = 1.0          # 高度比例

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "image_path": self.image_path,
            "threshold": self.threshold,
            "roi_x": self.roi_x,
            "roi_y": self.roi_y,
            "roi_w": self.roi_w,
            "roi_h": self.roi_h,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SceneAnchor':
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            image_path=data.get("image_path", ""),
            threshold=data.get("threshold", 0.85),
            roi_x=data.get("roi_x", 0.0),
            roi_y=data.get("roi_y", 0.0),
            roi_w=data.get("roi_w", 1.0),
            roi_h=data.get("roi_h", 1.0),
        )

@dataclass
class Scene:
    """场景模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "默认场景"
    description: str = ""
    recognition_image_path: Optional[str] = None
    recognition_threshold: float = 0.8
    actions: List[Action] = field(default_factory=list)
    is_default: bool = False
    enabled: bool = True
    next_scene_id: Optional[str] = None
    loop_count: int = 0
    # 新增：场景识别锚点列表
    anchors: List[SceneAnchor] = field(default_factory=list)

    def add_action(self, action: Action) -> Action:
        action.order = len(self.actions)
        self.actions.append(action)
        return action

    def remove_action(self, action_id: str) -> bool:
        for i, a in enumerate(self.actions):
            if a.id == action_id:
                self.actions.pop(i)
                self._reorder_actions()
                return True
        return False

    def get_action(self, action_id: str) -> Optional[Action]:
        for action in self.actions:
            if action.id == action_id:
                return action
        return None

    def move_action(self, action_id: str, direction: int) -> bool:
        for i, action in enumerate(self.actions):
            if action.id == action_id:
                new_index = i + direction
                if 0 <= new_index < len(self.actions):
                    self.actions[i], self.actions[new_index] = self.actions[new_index], self.actions[i]
                    self._reorder_actions()
                    return True
                break
        return False

    def _reorder_actions(self):
        for i, action in enumerate(self.actions):
            action.order = i

    def get_enabled_actions(self) -> List[Action]:
        return [a for a in sorted(self.actions, key=lambda x: x.order) if a.enabled]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "recognition_image_path": self.recognition_image_path,
            "recognition_threshold": self.recognition_threshold,
            "actions": [a.to_dict() for a in self.actions],
            "is_default": self.is_default,
            "enabled": self.enabled,
            "next_scene_id": self.next_scene_id,
            "loop_count": self.loop_count,
            "anchors": [anchor.to_dict() for anchor in self.anchors],  # 新增
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Scene':
        scene = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "默认场景"),
            description=data.get("description", ""),
            recognition_image_path=data.get("recognition_image_path"),
            recognition_threshold=data.get("recognition_threshold", 0.8),
            is_default=data.get("is_default", False),
            enabled=data.get("enabled", True),
            next_scene_id=data.get("next_scene_id"),
            loop_count=data.get("loop_count", 0),
        )
        scene.actions = [Action.from_dict(a) for a in data.get("actions", [])]
        # 新增：加载 anchors
        scene.anchors = [SceneAnchor.from_dict(a) for a in data.get("anchors", [])]
        return scene