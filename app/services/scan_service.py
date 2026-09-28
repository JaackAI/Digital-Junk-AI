from dataclasses import dataclass
from pathlib import Path

from app.database.database import Database
from app.duplicates.duplicate_detector import DuplicateDetector
from app.duplicates.duplicate_storage_service import (
    DuplicateStorageService,
)
from app.duplicates.near_duplicate_detector import (
    NearDuplicateDetector,
)
from app.duplicates.near_duplicate_storage_service import (
    NearDuplicateStorageService,
)
from app.scanner.file_scanner import FileScanner
from app.scanner.metadata import FileMetadata, MetadataExtractor


@dataclass
class ScanError:
    file_path: str
    error_message: str


@dataclass
class ScanResult:
    files: list[FileMetadata]
    errors: list[ScanError]
    scan_id: int | None = None

    @property
    def successful_count(self) -> int:
        return len(self.files)

    @property
    def failed_count(self) -> int:
        return len(self.errors)


class ScanService:
    """
    Coordinates directory validation, directory scanning,
    metadata extraction, exact duplicate detection,
    near-duplicate detection, and database persistence.
    """

    def __init__(
        self,
        scanner: FileScanner | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        database: Database | None = None,
    ):
        self.scanner = scanner or FileScanner()

        self.metadata_extractor = (
            metadata_extractor or MetadataExtractor()
        )

        self.database = database or Database()

        self.database.initialize()
        self.database.migrate_scan_statistics()
        self.database.migrate_duplicate_tables()
        self.database.migrate_near_duplicate_tables()

        # Exact duplicate detection
        self.duplicate_detector = DuplicateDetector()

        self.duplicate_storage_service = (
            DuplicateStorageService(
                database=self.database
            )
        )

        # Near-duplicate detection
        self.near_duplicate_detector = (
            NearDuplicateDetector(
                similarity_threshold=8
            )
        )

        self.near_duplicate_storage_service = (
            NearDuplicateStorageService(
                database=self.database
            )
        )

    def _validate_directory(
        self,
        directory: str,
    ) -> Path:
        if not directory or not directory.strip():
            raise ValueError(
                "Directory path cannot be empty."
            )

        directory_path = Path(
            directory.strip()
        )

        if not directory_path.exists():
            raise FileNotFoundError(
                f"Directory does not exist: {directory}"
            )

        if not directory_path.is_dir():
            raise NotADirectoryError(
                f"Path is not a directory: {directory}"
            )

        return directory_path

    def scan(
        self,
        directory: str,
        progress_callback=None,
    ) -> ScanResult:
        validated_directory = (
            self._validate_directory(directory)
        )

        directory = str(validated_directory)

        file_paths = self.scanner.scan_directory(
            directory
        )

        scan_id = self.database.create_scan(
            directory
        )

        result = ScanResult(
            files=[],
            errors=[],
            scan_id=scan_id,
        )

        total_files = len(file_paths)

        for index, file_path in enumerate(
            file_paths,
            start=1,
        ):
            if progress_callback is not None:
                progress_callback(
                    index,
                    total_files,
                    file_path,
                )

            try:
                metadata = (
                    self.metadata_extractor.extract(
                        file_path
                    )
                )

                result.files.append(metadata)

                self.database.save_file(
                    scan_id=scan_id,
                    metadata=metadata,
                )

            except (
                FileNotFoundError,
                PermissionError,
                OSError,
            ) as error:

                result.errors.append(
                    ScanError(
                        file_path=str(file_path),
                        error_message=str(error),
                    )
                )

            except Exception as error:

                result.errors.append(
                    ScanError(
                        file_path=str(file_path),
                        error_message=(
                            f"Unexpected error: {error}"
                        ),
                    )
                )

        # --------------------------------------------------
        # Scan statistics
        # --------------------------------------------------

        total_size_bytes = sum(
            metadata.size_bytes
            for metadata in result.files
        )

        self.database.update_scan_statistics(
            scan_id=scan_id,
            files_found=len(file_paths),
            files_processed=(
                result.successful_count
            ),
            files_failed=result.failed_count,
            total_size_bytes=(
                total_size_bytes
            ),
        )

        # --------------------------------------------------
        # Exact duplicate detection
        # --------------------------------------------------

        duplicate_groups = (
            self.duplicate_detector.find_duplicates(
                file_paths
            )
        )

        self.duplicate_storage_service.save_duplicate_groups(
            scan_id=scan_id,
            duplicate_groups=duplicate_groups,
        )

        # --------------------------------------------------
        # Near-duplicate detection
        # --------------------------------------------------

        near_duplicate_groups = (
            self.near_duplicate_detector
            .find_near_duplicates(
                file_paths
            )
        )

        self.near_duplicate_storage_service \
            .save_near_duplicate_groups(
                scan_id=scan_id,
                near_duplicate_groups=(
                    near_duplicate_groups
                ),
                similarity_threshold=8,
            )

        # --------------------------------------------------
        # Complete scan
        # --------------------------------------------------

        self.database.complete_scan(
            scan_id
        )

        return result