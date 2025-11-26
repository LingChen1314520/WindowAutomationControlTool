"""操作模型"""
from dataclasses import dataclass, field
from enum import Enum
import uuid


class ActionType(Enum):
    """操作类型"""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG = "drag"
    KEY_PRESS = "key_press"
    INPUT_TEXT = "input_text"
    WAIT = "wait"
    
    @classmethod
    def get_display_name(cls, action_type: 'ActionType') -> str:
        names = {
            cls.CLICK: "单击",
            cls.DOUBLE_CLICK: "双击",
            cls.RIGHT_CLICK: "右键单击",
            cls.DRAG: "拖拽",
            cls.KEY_PRESS: "按键",
            cls.INPUT_TEXT: "输入文本",
            cls.WAIT: "等待"
        }
        return names.get(action_type, action_type.value)


@dataclass
class Action:
    """操作模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    action_type: ActionType = ActionType.CLICK
    relative_x: float = 0.5
    relative_y: float = 0.5
    end_relative_x: float = 0.5
    end_relative_y: float = 0.5
    key: str = ""
    text: str = ""
    wait_time: int = 1000
    delay_after: int = 300
    description: str = ""
    order: int = 0
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "action_type": self.action_type.value,
            "relative_x": self.relative_x,
            "relative_y": self.relative_y,
            "end_relative_x": self.end_relative_x,
            "end_relative_y": self.end_relative_y,
            "key": self.key,
            "text": self.text,
            "wait_time": self.wait_time,
            "delay_after": self.delay_after,
            "description": self.description,
            "order": self.order,
            "enabled": self.enabled
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Action':
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            action_type=ActionType(data.get("action_type", "click")),
            relative_x=data.get("relative_x", 0.5),
            relative_y=data.get("relative_y", 0.5),
            end_relative_x=data.get("end_relative_x", 0.5),
            end_relative_y=data.get("end_relative_y", 0.5),
            key=data.get("key", ""),
            text=data.get("text", ""),
            wait_time=data.get("wait_time", 1000),
            delay_after=data.get("delay_after", 300),
            description=data.get("description", ""),
            order=data.get("order", 0),
            enabled=data.get("enabled", True)
        )