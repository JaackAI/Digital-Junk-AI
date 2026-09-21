from dataclasses import dataclass
from pathlib import Path

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
    Coordinates directory validation, directory scanning,
    metadata extraction, and database persistence.
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

        # Initialize database and ensure required
        # scan statistics columns exist.
        self.database.initialize()
        self.database.migrate_scan_statistics()

    # ==================================================
    # DIRECTORY VALIDATION
    # ==================================================

    def _validate_directory(self, directory: str) -> Path:
        """
        Validate the directory provided for scanning.

        Args:
            directory:
                Directory path supplied by the caller.

        Returns:
            A validated Path object.

        Raises:
            ValueError:
                If the directory path is empty.

            FileNotFoundError:
                If the directory does not exist.

            NotADirectoryError:
                If the path is not a directory.
        """

        # ----------------------------------------------
        # Validate input type/content
        # ----------------------------------------------

        if not directory or not directory.strip():
            raise ValueError(
                "Directory path cannot be empty."
            )

        directory_path = Path(directory.strip())

        # ----------------------------------------------
        # Check existence
        # ----------------------------------------------

        if not directory_path.exists():
            raise FileNotFoundError(
                f"Directory does not exist: {directory}"
            )

        # ----------------------------------------------
        # Check directory
        # ----------------------------------------------

        if not directory_path.is_dir():
            raise NotADirectoryError(
                f"Path is not a directory: {directory}"
            )

        return directory_path

    # ==================================================
    # SCAN
    # ==================================================

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
        # 1. VALIDATE DIRECTORY
        # ==================================================

        validated_directory = self._validate_directory(
            directory
        )

        # Use the normalized path from this point onward.
        directory = str(validated_directory)

        # ==================================================
        # 2. SCAN DIRECTORY
        # ==================================================

        file_paths = self.scanner.scan_directory(
            directory
        )

        # ==================================================
        # 3. CREATE SCAN RECORD
        # ==================================================

        scan_id = self.database.create_scan(
            directory
        )

        result = ScanResult(
            files=[],
            errors=[],
            scan_id=scan_id,
        )

        total_files = len(file_paths)

        # ==================================================
        # 4. PROCESS FILES
        # ==================================================

        for index, file_path in enumerate(
            file_paths,
            start=1,
        ):

            # ----------------------------------------------
            # Report progress
            # ----------------------------------------------

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
                # Save metadata
                # ------------------------------------------

                self.database.save_file(
                    scan_id=scan_id,
                    metadata=metadata,
                )

            # ==================================================
            # EXPECTED FILE ERRORS
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
            # UNEXPECTED FILE ERRORS
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
        # 5. CALCULATE TOTAL SIZE
        # ==================================================

        total_size_bytes = sum(
            metadata.size_bytes
            for metadata in result.files
        )

        # ==================================================
        # 6. UPDATE SCAN STATISTICS
        # ==================================================

        self.database.update_scan_statistics(
            scan_id=scan_id,
            files_found=len(file_paths),
            files_processed=result.successful_count,
            files_failed=result.failed_count,
            total_size_bytes=total_size_bytes,
        )

        # ==================================================
        # 7. MARK SCAN AS COMPLETED
        # ==================================================

        self.database.complete_scan(scan_id)

        # ==================================================
        # 8. RETURN RESULT
        # ==================================================

        return result