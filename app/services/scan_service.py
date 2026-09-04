from dataclasses import dataclass, field
from pathlib import Path

from app.scanner.file_scanner import FileScanner
from app.scanner.metadata import FileMetadata, MetadataExtractor


@dataclass
class ScanError:
    """
    Represents an error that occurred while processing a file.
    """

    file_path: str
    error_message: str


@dataclass
class ScanResult:
    """
    Represents the result of scanning a directory.
    """

    files: list[FileMetadata] = field(default_factory=list)
    errors: list[ScanError] = field(default_factory=list)

    @property
    def successful_count(self) -> int:
        return len(self.files)

    @property
    def failed_count(self) -> int:
        return len(self.errors)


class ScanService:
    """
    Coordinates file scanning and metadata extraction.
    """

    def __init__(
        self,
        scanner: FileScanner | None = None,
        metadata_extractor: MetadataExtractor | None = None,
    ):
        self.scanner = scanner or FileScanner()
        self.metadata_extractor = (
            metadata_extractor or MetadataExtractor()
        )

    def scan(self, directory_path: str) -> ScanResult:
        """
        Scan a directory and extract metadata from supported files.

        Args:
            directory_path: Directory to scan.

        Returns:
            ScanResult containing successfully processed files
            and processing errors.
        """

        file_paths = self.scanner.scan_directory(directory_path)

        result = ScanResult()

        for file_path in file_paths:
            try:
                metadata = self.metadata_extractor.extract(file_path)
                result.files.append(metadata)

            except (FileNotFoundError, PermissionError, OSError) as error:
                result.errors.append(
                    ScanError(
                        file_path=str(file_path),
                        error_message=str(error),
                    )
                )

        return result