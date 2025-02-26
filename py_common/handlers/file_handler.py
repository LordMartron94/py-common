import os
from pathlib import Path
from typing import List, Union

from typing_extensions import deprecated


class FileHandler:
    def is_file_of_type(self, file: Union[Path, str], extension: str) -> bool:
        return Path(file).is_file() and str(file).lower().endswith(extension)

    @deprecated("Use is_file_of_type instead.")
    def is_mp4_file(self, file: Union[Path, str]):
        """Check if the file has a .mp4 extension."""
        return Path(file).is_file() and str(file).lower().endswith('.mp4')

    @deprecated("Use is_file_of_type instead.")
    def is_ts_file(self, file: Union[Path, str]):
        return Path(file).is_file() and str(file).lower().endswith('.ts')

    def get_file_modified_date(self, file_path: str) -> float:
        """Get the modification time of a file."""
        return os.path.getmtime(file_path)

    def get_number_of_files_in_dir(self, directory: Path, extension: str = "*") -> int:
        if not directory.is_dir():
            raise ValueError("The provided path is not a valid directory.")

        # Count the number of files in the folder
        if extension == "*":
            num_files = sum(1 for _ in directory.iterdir() if _.is_file())
        else:
            num_files = sum(1 for _ in directory.iterdir() if self.is_file_of_type(_, extension))

        return num_files

    def get_children_paths(self, directory: Path, extension: str = "*", recursive=False) -> List[Path]:
        """
        Gets all the files with the given extension in the directory.

        Args:
            directory: The directory to search in.
            extension: The extension of the files to search for.
            Defaults to '*', to search for all files.
            recursive: Whether to search subfolders recursively.

        Returns:
            A list of paths to the files with the given extension.

        Raises:
            ValueError: If the provided path is not a valid directory.
        """
        if not directory.is_dir():
            raise ValueError("The provided path is not a valid directory.")

        paths: List[Path] = []
        items = [directory]  # Initialize with the starting directory

        num_processed_files: int = 0

        while items:
            current_item = items.pop()
            if current_item.is_dir():
                if recursive or num_processed_files == 0:
                    # Add subdirectories to the list for iterative processing
                    items.extend(current_item.iterdir())
            elif extension == "*" or (current_item.suffix == extension):
                paths.append(current_item)

            num_processed_files += 1

        return paths

    def get_children_paths_fast(self, directory: Path, extensions=None, recursive=False) -> List[Path]:
        """
        Gets all the files with the given extension in the directory, using os.walk for speed.

        Args:
            directory: The directory to search in.
            extensions: The extensions of the files to search for.
                Defaults to '*', to search for all files.
            recursive: Whether to search subfolders recursively.

        Returns:
            A list of paths to the files with the given extension.

        Raises:
            ValueError: If the provided path is not a valid directory.
        """

        if extensions is None:
            extensions = ["*"]

        if not directory.is_dir():
            raise ValueError("The provided path is not a valid directory.")

        paths: List[Path] = []

        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    filepath = Path(root) / file
                    if extensions == ["*"] or filepath.suffix in extensions:
                        paths.append(filepath)
        else:
            for item in directory.iterdir():
                if item.is_file() and (extensions == ["*"] or item.suffix in extensions):
                    paths.append(item)

        return paths

    def save_dict_to_file(self, data: dict, file_path: Path, header: str = None):
        with open(file_path, 'w') as file:
            if header is not None:
                file.write(f"{header}\n\n")

            for key, value in data.items():
                file.write(f"{key}: {value}\n")

    def get_children_directories(self, root_dir: Path, recursive:bool = False) -> List[Path]:
        if not root_dir.is_dir():
            raise ValueError("The provided path is not a valid directory.")

        directories: List[Path] = []
        items = []
        items.extend(root_dir.iterdir())

        while items:
            current_item = items.pop()
            if current_item.is_dir():
                directories.append(current_item)
                if recursive:
                    items.extend(current_item.iterdir())

        return directories
