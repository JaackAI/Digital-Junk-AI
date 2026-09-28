from pathlib import Path

from app.database.database import Database


class DuplicateStorageService:
    """
    Stores duplicate detection results in the database.
    """

    def __init__(
        self,
        database: Database | None = None,
    ):
        self.database = database or Database()

        self.database.initialize()
        self.database.migrate_scan_statistics()
        self.database.migrate_duplicate_tables()

    def save_duplicate_groups(
        self,
        scan_id: int,
        duplicate_groups: dict[str, list[Path]],
    ) -> int:
        """
        Save duplicate groups and their files.

        Args:
            scan_id: ID of the scan that produced the results.
            duplicate_groups: Mapping of file hash to duplicate
                file paths.

        Returns:
            Number of duplicate groups saved.
        """

        saved_group_count = 0

        for file_hash, file_paths in duplicate_groups.items():

            # A valid duplicate group must contain
            # at least two files.
            if len(file_paths) < 2:
                continue

            # --------------------------------------------------
            # Calculate total storage used by the group
            # --------------------------------------------------

            total_size_bytes = 0

            for file_path in file_paths:

                try:
                    total_size_bytes += (
                        file_path.stat().st_size
                    )

                except (
                    FileNotFoundError,
                    PermissionError,
                    OSError,
                ):
                    continue

            # --------------------------------------------------
            # Calculate storage occupied by duplicate copies
            # --------------------------------------------------

            duplicate_size_bytes = 0

            for file_path in file_paths[1:]:

                try:
                    duplicate_size_bytes += (
                        file_path.stat().st_size
                    )

                except (
                    FileNotFoundError,
                    PermissionError,
                    OSError,
                ):
                    continue

            # --------------------------------------------------
            # Save duplicate group
            # --------------------------------------------------

            duplicate_group_id = (
                self.database.save_duplicate_group(
                    scan_id=scan_id,
                    file_hash=file_hash,
                    file_count=len(file_paths),
                    total_size_bytes=total_size_bytes,
                    duplicate_size_bytes=duplicate_size_bytes,
                )
            )

            # --------------------------------------------------
            # Save individual duplicate files
            # --------------------------------------------------

            for file_path in file_paths:

                file_id = self._find_file_id(
                    scan_id=scan_id,
                    file_path=file_path,
                )

                # If the file was not successfully stored
                # in the files table, skip it.
                if file_id is None:
                    continue

                try:
                    file_size_bytes = (
                        file_path.stat().st_size
                    )

                except (
                    FileNotFoundError,
                    PermissionError,
                    OSError,
                ):
                    file_size_bytes = 0

                self.database.save_duplicate_file(
                    duplicate_group_id=duplicate_group_id,
                    file_id=file_id,
                    file_path=str(
                        Path(file_path).resolve()
                    ),
                    file_size_bytes=file_size_bytes,
                )

            saved_group_count += 1

        return saved_group_count

    def _find_file_id(
        self,
        scan_id: int,
        file_path: Path,
    ) -> int | None:
        """
        Find the database file ID for a scanned file.

        Both the incoming path and the stored database path
        are normalized before comparison. This prevents
        Windows path formatting differences from causing
        duplicate files to be skipped.
        """

        normalized_path = str(
            Path(file_path).resolve()
        )

        with self.database.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    file_path
                FROM files
                WHERE scan_id = ?
                """,
                (scan_id,),
            )

            rows = cursor.fetchall()

        # Compare normalized paths.
        for row in rows:

            stored_path = str(
                Path(row[1]).resolve()
            )

            if stored_path == normalized_path:
                return row[0]

        return None