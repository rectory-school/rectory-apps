"""Output types for views"""

from dataclasses import dataclass, field

from typing import Optional, List


@dataclass
class Icon:
    """An icon that can be displayed"""

    position: Optional[int]
    title: str
    icon: str


@dataclass
class LinkIcon(Icon):
    """An icon link to a website"""

    icon_type = 'link'
    url: str
    page_icon_id: int


@dataclass
class FolderIcon(Icon):
    """An icon button to launch a folder"""

    icon_type = 'folder'
    folder_id: int
    page_folder_id: int


@dataclass
class Folder:
    """A folder that can be shown in a modal"""

    folder_id: int
    title: str
    icons: List[LinkIcon] = field(default_factory=list)
