import hashlib
from pathlib import Path


class FileHashDetector:
    """
    Generates cryptographic hashes for files.

    SHA-256 is used to determine whether two files
    contain exactly the same data.
    """

    def __init__(self, chunk_size: int = 1024 * 1024):
        """
        Args:
            chunk_size:
                Number of bytes read from the file at a time.
                Default is 1 MB.
        """

        if chunk_size <= 0:
            raise ValueError(
                "Chunk size must be greater than zero."
            )

        self.chunk_size = chunk_size

    def calculate_sha256(
        self,
        file_path: str | Path,
    ) -> str:
        """
        Calculate the SHA-256 hash of a file.

        Args:
            file_path:
                Path to the file.

        Returns:
            SHA-256 hash as a hexadecimal string.
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

        sha256 = hashlib.sha256()

        with path.open("rb") as file:

            while True:

                chunk = file.read(
                    self.chunk_size
                )

                if not chunk:
                    break

                sha256.update(chunk)

        return sha256.hexdigest()