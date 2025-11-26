"""项目管理器"""
import os
import shutil
import json
from typing import List, Optional, Dict
from models import Project
import uuid


class ProjectManager:
    """项目管理器"""

    _instance = None
    GROUPS_FILE = "groups.json"

    def __new__(cls, data_dir: str = "data/projects"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.data_dir = data_dir
            cls._instance._projects = []
            cls._instance._groups = {}  # group_id -> group_name
            os.makedirs(data_dir, exist_ok=True)
            cls._instance._load_groups()
            cls._instance.load_all_projects()
        return cls._instance

    def _load_groups(self):
        """加载分组配置"""
        groups_file = os.path.join(self.data_dir, self.GROUPS_FILE)
        if os.path.exists(groups_file):
            try:
                with open(groups_file, 'r', encoding='utf-8') as f:
                    self._groups = json.load(f)
            except:
                self._groups = {}
        
        # 确保默认分组存在
        if "default" not in self._groups:
            self._groups["default"] = "默认分组"
        
        self._save_groups()

    def _save_groups(self):
        """保存分组配置"""
        groups_file = os.path.join(self.data_dir, self.GROUPS_FILE)
        with open(groups_file, 'w', encoding='utf-8') as f:
            json.dump(self._groups, f, ensure_ascii=False, indent=2)

    def get_groups(self) -> Dict[str, str]:
        """获取所有分组"""
        return self._groups.copy()

    def create_group(self, name: str) -> str:
        """创建分组，返回分组ID"""
        group_id = str(uuid.uuid4())[:8]
        self._groups[group_id] = name
        self._save_groups()
        return group_id

    def rename_group(self, group_id: str, new_name: str):
        """重命名分组"""
        if group_id in self._groups:
            self._groups[group_id] = new_name
            self._save_groups()

    def delete_group(self, group_id: str):
        """删除分组（项目移动到默认分组）"""
        if group_id != "default" and group_id in self._groups:
            # 将该分组的项目移动到默认分组
            for project in self._projects:
                if project.group_id == group_id:
                    project.group_id = "default"
                    self.save_project(project)
            
            del self._groups[group_id]
            self._save_groups()

    def get_group_name(self, group_id: str) -> str:
        """获取分组名称"""
        return self._groups.get(group_id, "默认分组")

    def move_project_to_group(self, project_id: str, group_id: str):
        """将项目移动到指定分组"""
        project = self.get_project(project_id)
        if project and group_id in self._groups:
            project.group_id = group_id
            self.save_project(project)

    def get_projects_by_group(self, group_id: str) -> List[Project]:
        """获取指定分组的项目"""
        return [p for p in self._projects if p.group_id == group_id]

    def load_all_projects(self):
        """加载所有项目"""
        self._projects = []
        if os.path.exists(self.data_dir):
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json') and filename != self.GROUPS_FILE:
                    filepath = os.path.join(self.data_dir, filename)
                    try:
                        project = Project.load(filepath)
                        # 确保分组存在
                        if project.group_id not in self._groups:
                            project.group_id = "default"
                        self._projects.append(project)
                    except Exception as e:
                        print(f"加载项目失败 {filename}: {e}")

    def get_all_projects(self) -> List[Project]:
        return sorted(self._projects, key=lambda p: p.updated_at, reverse=True)

    def get_project(self, project_id: str) -> Optional[Project]:
        for project in self._projects:
            if project.id == project_id:
                return project
        return None

    def create_project(self, name: str, description: str = "",
                       target_window_title: str = "", group_id: str = "default") -> Project:
        project = Project(
            name=name,
            description=description,
            target_window_title=target_window_title,
            group_id=group_id if group_id in self._groups else "default"
        )
        self._projects.append(project)
        self.save_project(project)
        return project

    def save_project(self, project: Project):
        project.save(self.data_dir)

    def delete_project(self, project_id: str) -> bool:
        project = self.get_project(project_id)
        if project:
            filepath = os.path.join(self.data_dir, f"{project_id}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
            
            image_dir = self.get_project_image_dir(project_id)
            if os.path.exists(image_dir):
                shutil.rmtree(image_dir)
            
            self._projects = [p for p in self._projects if p.id != project_id]
            return True
        return False

    def duplicate_project(self, project_id: str) -> Optional[Project]:
        project = self.get_project(project_id)
        if project:
            new_project = Project.from_dict(project.to_dict())
            new_project.id = str(uuid.uuid4())
            new_project.name = f"{project.name} - 副本"
            
            for scene in new_project.scenes:
                scene.id = str(uuid.uuid4())
                for action in scene.actions:
                    action.id = str(uuid.uuid4())
            
            self._projects.append(new_project)
            self.save_project(new_project)
            return new_project
        return None

    def get_project_image_dir(self, project_id: str) -> str:
        image_dir = os.path.join(self.data_dir, f"{project_id}_images")
        os.makedirs(image_dir, exist_ok=True)
        return image_dir

    def get_all_projects(self) -> List[Project]:
        """注意：不再排序，按 _projects 当前顺序返回"""
        return self._projects

    def move_project(self, project_id: str, direction: int):
        """
        移动项目顺序，direction: -1=上移, 1=下移
        只是调整内存中的顺序，重启程序后顺序可能恢复。
        """
        for i, p in enumerate(self._projects):
            if p.id == project_id:
                new_i = i + direction
                if 0 <= new_i < len(self._projects):
                    self._projects[i], self._projects[new_i] = self._projects[new_i], self._projects[i]
                    # 可选：保存一下，至少刷新 updated_at
                    self.save_project(self._projects[i])
                    self.save_project(self._projects[new_i])
                break