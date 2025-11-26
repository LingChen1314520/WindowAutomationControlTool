# ui/dialogs/__init__.py
from .project_dialog import ProjectDialog
from .scene_dialog import SceneDialog
from .action_dialog import ActionDialog
from .anchor_capture_dialog import AnchorCaptureDialog
from .scene_anchor_dialog import SceneAnchorDialog

__all__ = [
    'ProjectDialog',
    'SceneDialog',
    'ActionDialog',
    'AnchorCaptureDialog',
    'SceneAnchorDialog',
]