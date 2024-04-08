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

	def get_children_paths(self, directory: Path, extension: str) -> List[Path]:
		if not directory.is_dir():
			raise ValueError("The provided path is not a valid directory.")
		
		paths: List[Path] = []

		for file_path in directory.iterdir():
			if file_path.suffix == extension:
				paths.append(file_path)
		
		return paths
