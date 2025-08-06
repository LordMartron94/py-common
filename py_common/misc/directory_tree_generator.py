import fnmatch
from pathlib import Path
from typing import List, Union

from .directory_tree_config import DirectoryTreeConfig


class DirectoryTreeGenerator:
    """
    Generates a nicely formatted string representation of a directory tree
    and saves it to a file.

    The behavior is controlled by a DirectoryTreeConfig object.
    """

    # Box-drawing characters for the tree structure
    _PREFIX_MIDDLE = '├── '
    _PREFIX_LAST = '└── '
    _PREFIX_CONTINUE = '│   '
    _PREFIX_EMPTY = '    '

    def __init__(self, config: DirectoryTreeConfig):
        """
        Initializes the generator with a given configuration.

        Args:
            config: The configuration object specifying exclusions and other options.
        """
        self._config = config
        self._tree_lines: List[str] = []

    def generate(self, root_dir: Union[Path, str], output_file: Union[Path, str]) -> None:
        """
        Generates the directory tree and saves it to the specified output file.

        Args:
            root_dir: The path to the root directory to analyze.
            output_file: The path to the text file where the output will be saved.

        Raises:
            ValueError: If the root_dir is not a valid directory.
        """
        root_path = Path(root_dir)
        output_path = Path(output_file)

        if not root_path.is_dir():
            raise ValueError(f"Error: The provided root path '{root_dir}' is not a valid directory.")

        self._tree_lines = []
        self._tree_lines.append(f"{root_path.name}/")

        self._build_tree(directory=root_path, prefix="", depth=0)

        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the generated tree to the output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(self._tree_lines))

        print(f"Directory tree successfully saved to '{output_path}'")

    def _is_excluded(self, path: Path) -> bool:
        """Checks if a given path should be excluded based on the configuration."""
        if path.is_dir():
            return any(fnmatch.fnmatch(path.name, pattern) for pattern in self._config.exclude_dirs)

        if path.is_file():
            return any(fnmatch.fnmatch(path.name, pattern) for pattern in self._config.exclude_files)

        return False

    def _build_tree(self, directory: Path, prefix: str, depth: int):
        """
        Recursively builds the directory tree structure by coordinating helper methods.
        """
        # Depth check guard clause
        if self._config.max_depth is not None and depth > self._config.max_depth:
            return

        # Delegate fetching, filtering, and sorting to a helper
        children = self._get_prepared_children(directory)

        # Iterate through the prepared list of children
        for i, child in enumerate(children):
            is_last = (i == len(children) - 1)

            line = self._format_tree_entry(child, prefix, is_last)
            self._tree_lines.append(line)

            if child.is_dir():
                next_prefix = self._get_next_prefix(prefix, is_last)
                self._build_tree(directory=child, prefix=next_prefix, depth=depth + 1)

    def _get_prepared_children(self, directory: Path) -> List[Path]:
        """
        Gets the children of a directory, filters them according to the
        configuration, and sorts them for display.
        """
        # 1. Get all children, filtering out excluded ones
        children = [child for child in directory.iterdir() if not self._is_excluded(child)]

        # 2. If configured, filter out files
        if not self._config.show_files:
            children = [child for child in children if child.is_dir()]

        # 3. Sort children: directories first, then files, all alphabetically
        children.sort(key=lambda p: (p.is_file(), p.name.lower()))

        return children

    def _format_tree_entry(self, path: Path, prefix: str, is_last: bool) -> str:
        """Formats a single line of the directory tree."""
        connector = self._PREFIX_LAST if is_last else self._PREFIX_MIDDLE
        entry_name = f"{path.name}/" if path.is_dir() else path.name
        return f"{prefix}{connector}{entry_name}"

    def _get_next_prefix(self, prefix: str, is_last: bool) -> str:
        """Calculates the correct prefix for the next level of recursion."""
        return prefix + (self._PREFIX_EMPTY if is_last else self._PREFIX_CONTINUE)
