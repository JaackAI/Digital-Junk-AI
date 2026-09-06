from dataclasses import dataclass

from app.scanner.file_scanner import FileScanner
from app.scanner.metadata import FileMetadata, MetadataExtractor
from app.database.database import Database


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

        # Initialize database tables
        self.database.initialize()

        # Add scan statistics columns
        # to existing databases if required
        self.database.migrate_scan_statistics()

    def scan(self, directory: str) -> ScanResult:

        # --------------------------------------------------
        # 1. Scan directory
        # --------------------------------------------------

        file_paths = self.scanner.scan_directory(directory)

        # --------------------------------------------------
        # 2. Create scan record
        # --------------------------------------------------

        scan_id = self.database.create_scan(directory)

        result = ScanResult(
            files=[],
            errors=[],
            scan_id=scan_id,
        )

        # --------------------------------------------------
        # 3. Extract metadata and save files
        # --------------------------------------------------

        for file_path in file_paths:

            try:
                metadata = self.metadata_extractor.extract(
                    file_path
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

        # --------------------------------------------------
        # 4. Calculate total file size
        # --------------------------------------------------

        total_size_bytes = sum(
            metadata.size_bytes
            for metadata in result.files
        )

        # --------------------------------------------------
        # 5. Update scan statistics
        # --------------------------------------------------

        self.database.update_scan_statistics(
            scan_id=scan_id,
            files_found=len(file_paths),
            files_processed=result.successful_count,
            files_failed=result.failed_count,
            total_size_bytes=total_size_bytes,
        )

        # --------------------------------------------------
        # 6. Mark scan as completed
        # --------------------------------------------------

        self.database.complete_scan(scan_id)

        return result