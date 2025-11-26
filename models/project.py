"""项目模型"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import uuid
import json
import os
from .scene import Scene


@dataclass
class Project:
    """项目模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    target_window_title: str = ""
    target_window_class: str = ""
    scenes: List[Scene] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    auto_recognize_scene: bool = True
    recognize_interval: int = 2000
    loop_execution: bool = False
    max_loop_count: int = 0
    # 新增：分组ID
    group_id: str = "default"
    # 新增：是否折叠显示
    collapsed: bool = False

    def __post_init__(self):
        if not self.scenes:
            default_scene = Scene(name="默认场景", is_default=True)
            self.scenes.append(default_scene)
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()

    def add_scene(self, scene: Scene) -> Scene:
        self.scenes.append(scene)
        self.updated_at = datetime.now().isoformat()
        return scene

    def remove_scene(self, scene_id: str) -> bool:
        for i, s in enumerate(self.scenes):
            if s.id == scene_id and not s.is_default:
                self.scenes.pop(i)
                self.updated_at = datetime.now().isoformat()
                return True
        return False

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        for scene in self.scenes:
            if scene.id == scene_id:
                return scene
        return None

    def get_default_scene(self) -> Optional[Scene]:
        for scene in self.scenes:
            if scene.is_default:
                return scene
        return self.scenes[0] if self.scenes else None

    def get_enabled_scenes(self) -> List[Scene]:
        return [s for s in self.scenes if s.enabled]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "target_window_title": self.target_window_title,
            "target_window_class": self.target_window_class,
            "scenes": [s.to_dict() for s in self.scenes],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "auto_recognize_scene": self.auto_recognize_scene,
            "recognize_interval": self.recognize_interval,
            "loop_execution": self.loop_execution,
            "max_loop_count": self.max_loop_count,
            "group_id": self.group_id,
            "collapsed": self.collapsed
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        project = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            target_window_title=data.get("target_window_title", ""),
            target_window_class=data.get("target_window_class", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            auto_recognize_scene=data.get("auto_recognize_scene", True),
            recognize_interval=data.get("recognize_interval", 2000),
            loop_execution=data.get("loop_execution", False),
            max_loop_count=data.get("max_loop_count", 0),
            group_id=data.get("group_id", "default"),
            collapsed=data.get("collapsed", False)
        )
        project.scenes = [Scene.from_dict(s) for s in data.get("scenes", [])]
        if not project.scenes:
            project.scenes.append(Scene(name="默认场景", is_default=True))
        return project

    def save(self, directory: str):
        self.updated_at = datetime.now().isoformat()
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{self.id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'Project':
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def move_scene(self, scene_id: str, direction: int):
        """移动场景顺序，direction: -1 上移, 1 下移"""
        for i, s in enumerate(self.scenes):
            if s.id == scene_id:
                new_i = i + direction
                if 0 <= new_i < len(self.scenes):
                    self.scenes[i], self.scenes[new_i] = self.scenes[new_i], self.scenes[i]
                break