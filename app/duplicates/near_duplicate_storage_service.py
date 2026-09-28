from pathlib import Path

from app.database.database import Database


class NearDuplicateStorageService:
    """
    Stores near-duplicate detection results in the database.
    """

    def __init__(
        self,
        database: Database | None = None,
    ):
        self.database = database or Database()

        self.database.initialize()
        self.database.migrate_scan_statistics()
        self.database.migrate_duplicate_tables()
        self.database.migrate_near_duplicate_tables()

    def save_near_duplicate_groups(
        self,
        scan_id: int,
        near_duplicate_groups: dict[str, list[Path]],
        similarity_threshold: int,
    ) -> int:
        """
        Save near-duplicate groups and their files.

        Args:
            scan_id:
                ID of the scan that produced the results.

            near_duplicate_groups:
                Mapping of representative perceptual hash
                to near-duplicate file paths.

            similarity_threshold:
                Hamming-distance threshold used during
                near-duplicate detection.

        Returns:
            Number of near-duplicate groups saved.
        """

        if similarity_threshold < 0:
            raise ValueError(
                "Similarity threshold cannot be negative."
            )

        saved_group_count = 0

        for representative_hash, file_paths in (
            near_duplicate_groups.items()
        ):

            if len(file_paths) < 2:
                continue

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

            group_id = (
                self.database.save_near_duplicate_group(
                    scan_id=scan_id,
                    representative_hash=(
                        representative_hash
                    ),
                    file_count=len(file_paths),
                    total_size_bytes=(
                        total_size_bytes
                    ),
                    duplicate_size_bytes=(
                        duplicate_size_bytes
                    ),
                    similarity_threshold=(
                        similarity_threshold
                    ),
                )
            )

            files_saved = 0

            for file_path in file_paths:

                file_id = self._find_file_id(
                    scan_id=scan_id,
                    file_path=file_path,
                )

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

                perceptual_hash = (
                    self._calculate_perceptual_hash(
                        file_path
                    )
                )

                if perceptual_hash is None:
                    continue

                self.database.save_near_duplicate_file(
                    near_duplicate_group_id=group_id,
                    file_id=file_id,
                    file_path=str(
                        Path(file_path).resolve()
                    ),
                    file_size_bytes=file_size_bytes,
                    perceptual_hash=(
                        perceptual_hash
                    ),
                )

                files_saved += 1

            if files_saved > 0:
                saved_group_count += 1

        return saved_group_count

    def _find_file_id(
        self,
        scan_id: int,
        file_path: Path,
    ) -> int | None:
        """
        Find the database file ID for a scanned file.

        Paths are normalized before comparison so that
        Windows path formatting differences do not cause
        matching failures.
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

        for row in rows:

            stored_path = str(
                Path(row[1]).resolve()
            )

            if stored_path == normalized_path:
                return row[0]

        return None

    def _calculate_perceptual_hash(
        self,
        file_path: Path,
    ) -> str | None:
        """
        Calculate the perceptual hash for an image.

        Returns None if the image cannot be processed.
        """

        try:
            import imagehash
            from PIL import Image

            with Image.open(file_path) as image:
                perceptual_hash = imagehash.phash(
                    image
                )

            return str(perceptual_hash)

        except (
            FileNotFoundError,
            PermissionError,
            OSError,
            ValueError,
        ):
            return None

        except Exception:
            return None