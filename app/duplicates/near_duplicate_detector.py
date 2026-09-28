from pathlib import Path

from app.duplicates.perceptual_hash_detector import (
    PerceptualHashDetector,
)


class NearDuplicateDetector:
    """
    Detects visually similar image files using
    perceptual hashing.

    Unlike SHA-256 duplicate detection, this detector
    can identify images that are visually similar even
    when their binary data is different.
    """

    def __init__(
        self,
        perceptual_hash_detector: (
            PerceptualHashDetector | None
        ) = None,
        similarity_threshold: int = 8,
    ):
        if similarity_threshold < 0:
            raise ValueError(
                "Similarity threshold cannot be negative."
            )

        self.perceptual_hash_detector = (
            perceptual_hash_detector
            or PerceptualHashDetector()
        )

        self.similarity_threshold = (
            similarity_threshold
        )

    def find_near_duplicates(
        self,
        file_paths: list[Path],
    ) -> dict[str, list[Path]]:
        """
        Find groups of visually similar images.

        Args:
            file_paths:
                Image files to analyze.

        Returns:
            Dictionary mapping a representative hash
            to a list of visually similar image paths.
        """

        image_hashes = {}

        for file_path in file_paths:

            path = Path(file_path)

            if (
                path.suffix.lower()
                not in self.perceptual_hash_detector
                .SUPPORTED_EXTENSIONS
            ):
                continue

            try:

                image_hash = (
                    self.perceptual_hash_detector
                    .calculate_phash(path)
                )

                image_hashes[path] = image_hash

            except (
                FileNotFoundError,
                PermissionError,
                OSError,
                ValueError,
            ):

                continue

            except Exception:

                continue

        near_duplicate_groups = []

        processed_files = set()

        paths = list(image_hashes.keys())

        for index, first_path in enumerate(paths):

            if first_path in processed_files:
                continue

            group = [first_path]

            first_hash = image_hashes[first_path]

            for second_path in paths[index + 1:]:

                if second_path in processed_files:
                    continue

                second_hash = image_hashes[second_path]

                distance = (
                    self.perceptual_hash_detector
                    .calculate_distance(
                        first_hash,
                        second_hash,
                    )
                )

                if (
                    distance
                    <= self.similarity_threshold
                ):

                    group.append(second_path)

            if len(group) > 1:

                near_duplicate_groups.append(
                    group
                )

                processed_files.update(group)

        result = {}

        for group in near_duplicate_groups:

            representative_hash = str(
                image_hashes[group[0]]
            )

            result[
                representative_hash
            ] = group

        return result

    def get_near_duplicate_file_count(
        self,
        near_duplicate_groups: dict[
            str,
            list[Path],
        ],
    ) -> int:
        """
        Return the total number of files contained
        in near-duplicate groups.
        """

        return sum(
            len(paths)
            for paths in near_duplicate_groups.values()
        )

    def get_near_duplicate_group_count(
        self,
        near_duplicate_groups: dict[
            str,
            list[Path],
        ],
    ) -> int:
        """
        Return the number of near-duplicate groups.
        """

        return len(near_duplicate_groups)

    def get_near_duplicate_storage_bytes(
        self,
        near_duplicate_groups: dict[
            str,
            list[Path],
        ],
    ) -> int:
        """
        Calculate storage occupied by additional copies
        in near-duplicate groups.

        The first file in each group is treated as the
        representative file. Remaining files are counted
        as potentially recoverable storage.
        """

        duplicate_storage = 0

        for paths in near_duplicate_groups.values():

            for file_path in paths[1:]:

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