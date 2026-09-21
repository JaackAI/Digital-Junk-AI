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
    """
    Coordinates directory scanning, metadata extraction,
    and database persistence.
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

        # Initialize database and ensure scan statistics
        # columns exist.
        self.database.initialize()
        self.database.migrate_scan_statistics()

    def scan(
        self,
        directory: str,
        progress_callback=None,
    ) -> ScanResult:
        """
        Scan a directory and optionally report progress.

        Args:
            directory:
                Directory to scan.

            progress_callback:
                Optional callback receiving:
                current file number,
                total files,
                current file path.

        Returns:
            ScanResult containing successfully processed
            files and file-level errors.
        """

        # ==================================================
        # 1. SCAN DIRECTORY
        # ==================================================

        file_paths = self.scanner.scan_directory(directory)

        # ==================================================
        # 2. CREATE SCAN RECORD
        # ==================================================

        scan_id = self.database.create_scan(directory)

        result = ScanResult(
            files=[],
            errors=[],
            scan_id=scan_id,
        )

        total_files = len(file_paths)

        # ==================================================
        # 3. PROCESS EACH FILE
        # ==================================================

        for index, file_path in enumerate(
            file_paths,
            start=1,
        ):

            # Report progress before processing the file.
            if progress_callback is not None:

                progress_callback(
                    index,
                    total_files,
                    file_path,
                )

            try:

                # ------------------------------------------
                # Extract metadata
                # ------------------------------------------

                metadata = self.metadata_extractor.extract(
                    file_path
                )

                # ------------------------------------------
                # Store successful result
                # ------------------------------------------

                result.files.append(metadata)

                # ------------------------------------------
                # Save metadata to database
                # ------------------------------------------

                self.database.save_file(
                    scan_id=scan_id,
                    metadata=metadata,
                )

            # ==================================================
            # EXPECTED FILE-LEVEL ERRORS
            # ==================================================

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

            # ==================================================
            # UNEXPECTED FILE-LEVEL ERRORS
            # ==================================================

            except Exception as error:

                result.errors.append(
                    ScanError(
                        file_path=str(file_path),
                        error_message=(
                            f"Unexpected error: {error}"
                        ),
                    )
                )

        # ==================================================
        # 4. CALCULATE TOTAL SIZE
        # ==================================================

        total_size_bytes = sum(
            metadata.size_bytes
            for metadata in result.files
        )

        # ==================================================
        # 5. UPDATE SCAN STATISTICS
        # ==================================================

        self.database.update_scan_statistics(
            scan_id=scan_id,
            files_found=len(file_paths),
            files_processed=result.successful_count,
            files_failed=result.failed_count,
            total_size_bytes=total_size_bytes,
        )

        # ==================================================
        # 6. MARK SCAN AS COMPLETED
        # ==================================================

        self.database.complete_scan(scan_id)

        # ==================================================
        # 7. RETURN RESULT
        # ==================================================

        return result