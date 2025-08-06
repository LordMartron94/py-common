from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DirectoryTreeConfig:
    """
    Configuration object for the DirectoryTreeGenerator.

    Attributes:
        exclude_dirs: A list of directory names to exclude.
                      Supports glob patterns (e.g., "*_cache").
        exclude_files: A list of file names to exclude.
                       Supports glob patterns (e.g., "*.log", "temp_*").
        max_depth: The maximum depth to traverse into the directory structure.
                   `None` means no limit. A depth of 0 shows only the root content.
        show_files: If False, only the directory structure will be shown.
    """
    exclude_dirs: List[str] = field(default_factory=lambda: ['.git', '__pycache__', '.vscode'])
    exclude_files: List[str] = field(default_factory=lambda: ['.DS_Store', '*.tmp', '*.log'])
    max_depth: Optional[int] = None
    show_files: bool = True
