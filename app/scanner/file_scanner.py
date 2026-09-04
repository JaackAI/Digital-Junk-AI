from pathlib import Path


class FileScanner:
    """
    Scans directories recursively and returns supported files.
    """

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".pdf",
        ".txt",
        ".docx",
        ".csv",
        ".xlsx",
    }

    def scan_directory(self, directory_path: str) -> list[Path]:
        """
        Recursively scan a directory and return supported files.

        Args:
            directory_path: Path of the directory to scan.

        Returns:
            A list of supported file paths.
        """

        directory = Path(directory_path)

        if not directory.exists():
            raise FileNotFoundError(
                f"Directory does not exist: {directory_path}"
            )

        if not directory.is_dir():
            raise NotADirectoryError(
                f"Path is not a directory: {directory_path}"
            )

        supported_files = []

        for file_path in directory.rglob("*"):

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                supported_files.append(file_path)

        return supported_files