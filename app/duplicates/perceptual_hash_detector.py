from pathlib import Path

import imagehash
from PIL import Image


class PerceptualHashDetector:
    """
    Generates perceptual hashes for image files.

    Perceptual hashing is used to identify images that
    are visually similar even when their binary data
    is different.
    """

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    def __init__(self):
        pass

    def calculate_phash(
        self,
        file_path: str | Path,
    ) -> imagehash.ImageHash:
        """
        Calculate the perceptual hash of an image.

        Args:
            file_path: Path to the image file.

        Returns:
            Perceptual hash of the image.

        Raises:
            FileNotFoundError:
                If the file does not exist.
            ValueError:
                If the file is not a supported image.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File does not exist: {file_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported image format: {path.suffix}"
            )

        with Image.open(path) as image:

            return imagehash.phash(image)

    def calculate_distance(
        self,
        hash1: imagehash.ImageHash,
        hash2: imagehash.ImageHash,
    ) -> int:
        """
        Calculate the Hamming distance between two
        perceptual hashes.

        A smaller distance means the images are
        more visually similar.
        """

        return hash1 - hash2

    def are_similar(
        self,
        hash1: imagehash.ImageHash,
        hash2: imagehash.ImageHash,
        threshold: int = 8,
    ) -> bool:
        """
        Determine whether two images are visually similar.

        Args:
            hash1: First perceptual hash.
            hash2: Second perceptual hash.
            threshold: Maximum allowed Hamming distance.

        Returns:
            True if the images are considered similar.
        """

        if threshold < 0:
            raise ValueError(
                "Threshold cannot be negative."
            )

        distance = self.calculate_distance(
            hash1,
            hash2,
        )

        return distance <= threshold