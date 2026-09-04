from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import mimetypes


@dataclass
class FileMetadata:
    """
    Represents basic metadata extracted from a file.
    """

    file_name: str
    file_path: str
    extension: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    accessed_at: datetime
    mime_type: str | None


class MetadataExtractor:
    """
    Extracts metadata from files.
    """

    def extract(self, file_path: Path) -> FileMetadata:
        """
        Extract metadata from a single file.

        Args:
            file_path: Path object representing the file.

        Returns:
            FileMetadata containing the extracted information.
        """

        if not file_path.exists():
            raise FileNotFoundError(
                f"File does not exist: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        file_stats = file_path.stat()

        mime_type, _ = mimetypes.guess_type(
            str(file_path)
        )

        return FileMetadata(
            file_name=file_path.name,
            file_path=str(file_path.resolve()),
            extension=file_path.suffix.lower(),
            size_bytes=file_stats.st_size,
            created_at=datetime.fromtimestamp(
                file_stats.st_ctime
            ),
            modified_at=datetime.fromtimestamp(
                file_stats.st_mtime
            ),
            accessed_at=datetime.fromtimestamp(
                file_stats.st_atime
            ),
            mime_type=mime_type,
        )