from pathlib import Path

from app.duplicates.hash_detector import FileHashDetector


class DuplicateDetector:
    """
    Detects exact duplicate files using SHA-256 hashes.
    """

    def __init__(
        self,
        hash_detector: FileHashDetector | None = None,
    ):
        """
        Initialize the duplicate detector.

        Args:
            hash_detector:
                Optional FileHashDetector instance.
        """

        self.hash_detector = (
            hash_detector or FileHashDetector()
        )

    def find_duplicates(
        self,
        file_paths: list[Path],
    ) -> dict[str, list[Path]]:
        """
        Find exact duplicate files.

        Files are grouped by their SHA-256 hash.

        Args:
            file_paths:
                List of file paths to analyze.

        Returns:
            Dictionary where:
                key = SHA-256 hash
                value = list of files with that hash

            Only groups containing more than one file
            are returned.
        """

        hash_groups: dict[str, list[Path]] = {}

        for file_path in file_paths:

            try:

                file_hash = (
                    self.hash_detector.calculate_sha256(
                        file_path
                    )
                )

                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []

                hash_groups[file_hash].append(
                    Path(file_path)
                )

            except (
                FileNotFoundError,
                PermissionError,
                OSError,
            ):
                # Ignore files that cannot be read.
                continue

            except Exception:
                # Prevent one problematic file from
                # stopping the entire duplicate scan.
                continue

        duplicate_groups = {
            file_hash: paths
            for file_hash, paths in hash_groups.items()
            if len(paths) > 1
        }

        return duplicate_groups

    def get_duplicate_file_count(
        self,
        duplicate_groups: dict[str, list[Path]],
    ) -> int:
        """
        Return the total number of files involved
        in duplicate groups.
        """

        return sum(
            len(paths)
            for paths in duplicate_groups.values()
        )

    def get_duplicate_group_count(
        self,
        duplicate_groups: dict[str, list[Path]],
    ) -> int:
        """
        Return the number of duplicate groups.
        """

        return len(duplicate_groups)

    def get_duplicate_storage_bytes(
        self,
        duplicate_groups: dict[str, list[Path]],
    ) -> int:
        """
        Calculate potential duplicate storage.

        For each duplicate group, the first file is
        considered the original and the remaining files
        are considered duplicate copies.

        Returns:
            Number of bytes potentially occupied by
            duplicate copies.
        """

        duplicate_storage = 0

        for paths in duplicate_groups.values():

            # Keep one copy as the original.
            duplicate_paths = paths[1:]

            for file_path in duplicate_paths:

                try:

                    duplicate_storage += (
                        file_path.stat().st_size
                    )

                except (
                    FileNotFoundError,
                    PermissionError,
                    OSError,
                ):
                    continue

        return duplicate_storage