import sqlite3
from datetime import datetime
from pathlib import Path

from app.scanner.metadata import FileMetadata


class Database:
    """
    Handles SQLite database operations for Digital Junk AI.
    """

    def __init__(
        self,
        database_path: str = "data/digital_junk_ai.db",
    ):
        self.database_path = Path(database_path)

        # Make sure the parent directory exists.
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ==================================================
    # CONNECTION
    # ==================================================

    def get_connection(self) -> sqlite3.Connection:
        """
        Create and return a SQLite database connection.
        """

        connection = sqlite3.connect(
            self.database_path
        )

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    # ==================================================
    # DATABASE INITIALIZATION
    # ==================================================

    def initialize(self) -> None:
        """
        Create the core database tables if they do not exist.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            # ==================================================
            # SCANS TABLE
            # ==================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    directory_path TEXT NOT NULL,

                    started_at TEXT NOT NULL,

                    completed_at TEXT,

                    files_found INTEGER NOT NULL DEFAULT 0,

                    files_processed INTEGER NOT NULL DEFAULT 0,

                    files_failed INTEGER NOT NULL DEFAULT 0,

                    total_size_bytes INTEGER NOT NULL DEFAULT 0
                )
                """
            )

            # ==================================================
            # FILES TABLE
            # ==================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    scan_id INTEGER NOT NULL,

                    file_name TEXT NOT NULL,

                    file_path TEXT NOT NULL,

                    extension TEXT,

                    size_bytes INTEGER NOT NULL,

                    created_at TEXT,

                    modified_at TEXT,

                    accessed_at TEXT,

                    mime_type TEXT,

                    FOREIGN KEY (scan_id)
                        REFERENCES scans(id)
                        ON DELETE CASCADE
                )
                """
            )

            connection.commit()

    # ==================================================
    # SCAN STATISTICS MIGRATION
    # ==================================================

    def migrate_scan_statistics(self) -> None:
        """
        Add scan statistics columns if they are missing.

        This keeps older databases compatible with the
        current application.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                PRAGMA table_info(scans)
                """
            )

            columns = {
                row[1]
                for row in cursor.fetchall()
            }

            if "files_found" not in columns:

                cursor.execute(
                    """
                    ALTER TABLE scans
                    ADD COLUMN files_found
                    INTEGER NOT NULL DEFAULT 0
                    """
                )

            if "files_processed" not in columns:

                cursor.execute(
                    """
                    ALTER TABLE scans
                    ADD COLUMN files_processed
                    INTEGER NOT NULL DEFAULT 0
                    """
                )

            if "files_failed" not in columns:

                cursor.execute(
                    """
                    ALTER TABLE scans
                    ADD COLUMN files_failed
                    INTEGER NOT NULL DEFAULT 0
                    """
                )

            if "total_size_bytes" not in columns:

                cursor.execute(
                    """
                    ALTER TABLE scans
                    ADD COLUMN total_size_bytes
                    INTEGER NOT NULL DEFAULT 0
                    """
                )

            connection.commit()

    # ==================================================
    # DUPLICATE TABLE MIGRATION
    # ==================================================

    def migrate_duplicate_tables(self) -> None:
        """
        Create duplicate detection tables if they do not exist.

        Existing scan and file data is preserved.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            # ==================================================
            # DUPLICATE GROUPS
            # ==================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS duplicate_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    scan_id INTEGER NOT NULL,

                    file_hash TEXT NOT NULL,

                    file_count INTEGER NOT NULL,

                    total_size_bytes INTEGER NOT NULL DEFAULT 0,

                    duplicate_size_bytes INTEGER NOT NULL DEFAULT 0,

                    created_at TEXT NOT NULL,

                    FOREIGN KEY (scan_id)
                        REFERENCES scans(id)
                        ON DELETE CASCADE
                )
                """
            )

            # ==================================================
            # DUPLICATE FILES
            # ==================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS duplicate_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    duplicate_group_id INTEGER NOT NULL,

                    file_id INTEGER NOT NULL,

                    file_path TEXT NOT NULL,

                    file_size_bytes INTEGER NOT NULL DEFAULT 0,

                    FOREIGN KEY (duplicate_group_id)
                        REFERENCES duplicate_groups(id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (file_id)
                        REFERENCES files(id)
                        ON DELETE CASCADE
                )
                """
            )

            # ==================================================
            # INDEXES
            # ==================================================

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_duplicate_groups_scan_id
                ON duplicate_groups(scan_id)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_duplicate_groups_file_hash
                ON duplicate_groups(file_hash)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_duplicate_files_group_id
                ON duplicate_files(duplicate_group_id)
                """
            )

            connection.commit()

    # ==================================================
    # NEAR-DUPLICATE TABLE MIGRATION
    # ==================================================

    def migrate_near_duplicate_tables(self) -> None:
        """
        Create near-duplicate detection tables if they
        do not already exist.

        Near duplicates are visually similar images
        detected using perceptual hashing.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            # ==================================================
            # NEAR-DUPLICATE GROUPS
            # ==================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS near_duplicate_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    scan_id INTEGER NOT NULL,

                    representative_hash TEXT NOT NULL,

                    file_count INTEGER NOT NULL,

                    total_size_bytes INTEGER NOT NULL DEFAULT 0,

                    duplicate_size_bytes INTEGER NOT NULL DEFAULT 0,

                    similarity_threshold INTEGER NOT NULL,

                    created_at TEXT NOT NULL,

                    FOREIGN KEY (scan_id)
                        REFERENCES scans(id)
                        ON DELETE CASCADE
                )
                """
            )

            # ==================================================
            # NEAR-DUPLICATE FILES
            # ==================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS near_duplicate_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    near_duplicate_group_id INTEGER NOT NULL,

                    file_id INTEGER NOT NULL,

                    file_path TEXT NOT NULL,

                    file_size_bytes INTEGER NOT NULL DEFAULT 0,

                    perceptual_hash TEXT NOT NULL,

                    FOREIGN KEY (near_duplicate_group_id)
                        REFERENCES near_duplicate_groups(id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (file_id)
                        REFERENCES files(id)
                        ON DELETE CASCADE
                )
                """
            )

            # ==================================================
            # INDEXES
            # ==================================================

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_near_duplicate_groups_scan_id
                ON near_duplicate_groups(scan_id)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_near_duplicate_groups_hash
                ON near_duplicate_groups(
                    representative_hash
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_near_duplicate_files_group_id
                ON near_duplicate_files(
                    near_duplicate_group_id
                )
                """
            )

            connection.commit()

    # ==================================================
    # CREATE SCAN
    # ==================================================

    def create_scan(
        self,
        directory_path: str,
    ) -> int:
        """
        Create a new scan record.

        Returns:
            ID of the newly created scan.
        """

        started_at = datetime.now().isoformat()

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO scans (
                    directory_path,
                    started_at
                )
                VALUES (?, ?)
                """,
                (
                    directory_path,
                    started_at,
                ),
            )

            scan_id = cursor.lastrowid

            connection.commit()

        return scan_id

    # ==================================================
    # SAVE FILE
    # ==================================================

    def save_file(
        self,
        scan_id: int,
        metadata: FileMetadata,
    ) -> int:
        """
        Save extracted file metadata.

        Returns:
            ID of the newly inserted file.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO files (
                    scan_id,
                    file_name,
                    file_path,
                    extension,
                    size_bytes,
                    created_at,
                    modified_at,
                    accessed_at,
                    mime_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    metadata.file_name,
                    metadata.file_path,
                    metadata.extension,
                    metadata.size_bytes,
                    metadata.created_at,
                    metadata.modified_at,
                    metadata.accessed_at,
                    metadata.mime_type,
                ),
            )

            file_id = cursor.lastrowid

            connection.commit()

        return file_id

    # ==================================================
    # COMPLETE SCAN
    # ==================================================

    def complete_scan(
        self,
        scan_id: int,
    ) -> None:
        """
        Mark a scan as completed.
        """

        completed_at = datetime.now().isoformat()

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE scans
                SET completed_at = ?
                WHERE id = ?
                """,
                (
                    completed_at,
                    scan_id,
                ),
            )

            connection.commit()

    # ==================================================
    # UPDATE SCAN STATISTICS
    # ==================================================

    def update_scan_statistics(
        self,
        scan_id: int,
        files_found: int,
        files_processed: int,
        files_failed: int,
        total_size_bytes: int,
    ) -> None:
        """
        Update statistics for a scan.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE scans
                SET
                    files_found = ?,
                    files_processed = ?,
                    files_failed = ?,
                    total_size_bytes = ?
                WHERE id = ?
                """,
                (
                    files_found,
                    files_processed,
                    files_failed,
                    total_size_bytes,
                    scan_id,
                ),
            )

            connection.commit()

    # ==================================================
    # SCAN HISTORY
    # ==================================================

    def get_scan_history(self) -> list[dict]:
        """
        Return all scans, newest first.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    directory_path,
                    started_at,
                    completed_at,
                    files_found,
                    files_processed,
                    files_failed,
                    total_size_bytes
                FROM scans
                ORDER BY id DESC
                """
            )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "directory_path": row[1],
                "started_at": row[2],
                "completed_at": row[3],
                "files_found": row[4],
                "files_processed": row[5],
                "files_failed": row[6],
                "total_size_bytes": row[7],
            }
            for row in rows
        ]

    # ==================================================
    # GET SCAN BY ID
    # ==================================================

    def get_scan_by_id(
        self,
        scan_id: int,
    ) -> dict | None:
        """
        Return a scan by ID.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    directory_path,
                    started_at,
                    completed_at,
                    files_found,
                    files_processed,
                    files_failed,
                    total_size_bytes
                FROM scans
                WHERE id = ?
                """,
                (scan_id,),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "directory_path": row[1],
            "started_at": row[2],
            "completed_at": row[3],
            "files_found": row[4],
            "files_processed": row[5],
            "files_failed": row[6],
            "total_size_bytes": row[7],
        }

    # ==================================================
    # GET FILES BY SCAN
    # ==================================================

    def get_files_by_scan(
        self,
        scan_id: int,
    ) -> list[dict]:
        """
        Return all files belonging to a scan.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    scan_id,
                    file_name,
                    file_path,
                    extension,
                    size_bytes,
                    created_at,
                    modified_at,
                    accessed_at,
                    mime_type
                FROM files
                WHERE scan_id = ?
                ORDER BY id
                """,
                (scan_id,),
            )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "scan_id": row[1],
                "file_name": row[2],
                "file_path": row[3],
                "extension": row[4],
                "size_bytes": row[5],
                "created_at": row[6],
                "modified_at": row[7],
                "accessed_at": row[8],
                "mime_type": row[9],
            }
            for row in rows
        ]

    # ==================================================
    # LATEST SCAN
    # ==================================================

    def get_latest_scan(self) -> dict | None:
        """
        Return the most recent scan.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    directory_path,
                    started_at,
                    completed_at,
                    files_found,
                    files_processed,
                    files_failed,
                    total_size_bytes
                FROM scans
                ORDER BY id DESC
                LIMIT 1
                """
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "directory_path": row[1],
            "started_at": row[2],
            "completed_at": row[3],
            "files_found": row[4],
            "files_processed": row[5],
            "files_failed": row[6],
            "total_size_bytes": row[7],
        }

    # ==================================================
    # STORAGE SUMMARY
    # ==================================================

    def get_storage_summary(self) -> dict:
        """
        Return total file count and storage usage.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_files,
                    COALESCE(
                        SUM(size_bytes),
                        0
                    ) AS total_size_bytes
                FROM files
                """
            )

            row = cursor.fetchone()

        return {
            "total_files": row[0],
            "total_size_bytes": row[1],
        }

    # ==================================================
    # STORAGE BY EXTENSION
    # ==================================================

    def get_storage_by_extension(
        self,
    ) -> list[dict]:
        """
        Return storage grouped by extension.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    extension,
                    COUNT(*) AS file_count,
                    COALESCE(
                        SUM(size_bytes),
                        0
                    ) AS total_size_bytes
                FROM files
                GROUP BY extension
                ORDER BY total_size_bytes DESC
                """
            )

            rows = cursor.fetchall()

        return [
            {
                "extension": row[0],
                "file_count": row[1],
                "total_size_bytes": row[2],
            }
            for row in rows
        ]

    # ==================================================
    # STORAGE BY CATEGORY
    # ==================================================

    def get_storage_by_category(
        self,
    ) -> list[dict]:
        """
        Return storage grouped into user-friendly categories.
        """

        category_map = {
            ".jpg": "Images",
            ".jpeg": "Images",
            ".png": "Images",
            ".webp": "Images",
            ".docx": "Documents",
            ".txt": "Documents",
            ".csv": "Documents",
            ".xlsx": "Documents",
            ".pdf": "PDFs",
        }

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    extension,
                    COUNT(*) AS file_count,
                    COALESCE(
                        SUM(size_bytes),
                        0
                    ) AS total_size_bytes
                FROM files
                GROUP BY extension
                ORDER BY total_size_bytes DESC
                """
            )

            rows = cursor.fetchall()

        categories = {}

        for row in rows:

            extension = row[0]

            file_count = row[1]

            total_size_bytes = row[2]

            category = category_map.get(
                extension.lower()
                if extension
                else "",
                "Other",
            )

            if category not in categories:

                categories[category] = {
                    "category": category,
                    "file_count": 0,
                    "total_size_bytes": 0,
                }

            categories[category][
                "file_count"
            ] += file_count

            categories[category][
                "total_size_bytes"
            ] += total_size_bytes

        return sorted(
            categories.values(),
            key=lambda item: item[
                "total_size_bytes"
            ],
            reverse=True,
        )

    # ==================================================
    # LARGEST FILES
    # ==================================================

    def get_largest_files(
        self,
        limit: int = 10,
    ) -> list[dict]:
        """
        Return the largest files.
        """

        if limit <= 0:
            return []

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    scan_id,
                    file_name,
                    file_path,
                    extension,
                    size_bytes,
                    created_at,
                    modified_at,
                    accessed_at,
                    mime_type
                FROM files
                ORDER BY size_bytes DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "scan_id": row[1],
                "file_name": row[2],
                "file_path": row[3],
                "extension": row[4],
                "size_bytes": row[5],
                "created_at": row[6],
                "modified_at": row[7],
                "accessed_at": row[8],
                "mime_type": row[9],
            }
            for row in rows
        ]

    # ==================================================
    # LATEST SCAN STORAGE SUMMARY
    # ==================================================

    def get_latest_scan_storage_summary(
        self,
    ) -> dict:
        """
        Return storage summary for the latest scan.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_files,
                    COALESCE(
                        SUM(size_bytes),
                        0
                    )
                FROM files
                WHERE scan_id = (
                    SELECT id
                    FROM scans
                    ORDER BY id DESC
                    LIMIT 1
                )
                """
            )

            row = cursor.fetchone()

        return {
            "total_files": row[0],
            "total_size_bytes": row[1],
        }

    # ==================================================
    # LATEST SCAN STORAGE BY CATEGORY
    # ==================================================

    def get_latest_scan_storage_by_category(
        self,
    ) -> list[dict]:
        """
        Return category storage for the latest scan.
        """

        category_map = {
            ".jpg": "Images",
            ".jpeg": "Images",
            ".png": "Images",
            ".webp": "Images",
            ".docx": "Documents",
            ".txt": "Documents",
            ".csv": "Documents",
            ".xlsx": "Documents",
            ".pdf": "PDFs",
        }

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    extension,
                    COUNT(*) AS file_count,
                    COALESCE(
                        SUM(size_bytes),
                        0
                    ) AS total_size_bytes
                FROM files
                WHERE scan_id = (
                    SELECT id
                    FROM scans
                    ORDER BY id DESC
                    LIMIT 1
                )
                GROUP BY extension
                ORDER BY total_size_bytes DESC
                """
            )

            rows = cursor.fetchall()

        categories = {}

        for row in rows:

            extension = row[0]

            file_count = row[1]

            total_size_bytes = row[2]

            category = category_map.get(
                extension.lower()
                if extension
                else "",
                "Other",
            )

            if category not in categories:

                categories[category] = {
                    "category": category,
                    "file_count": 0,
                    "total_size_bytes": 0,
                }

            categories[category][
                "file_count"
            ] += file_count

            categories[category][
                "total_size_bytes"
            ] += total_size_bytes

        return sorted(
            categories.values(),
            key=lambda item: item[
                "total_size_bytes"
            ],
            reverse=True,
        )

    # ==================================================
    # LATEST SCAN LARGEST FILES
    # ==================================================

    def get_latest_scan_largest_files(
        self,
        limit: int = 10,
    ) -> list[dict]:
        """
        Return largest files from the latest scan.
        """

        if limit <= 0:
            return []

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    scan_id,
                    file_name,
                    file_path,
                    extension,
                    size_bytes,
                    created_at,
                    modified_at,
                    accessed_at,
                    mime_type
                FROM files
                WHERE scan_id = (
                    SELECT id
                    FROM scans
                    ORDER BY id DESC
                    LIMIT 1
                )
                ORDER BY size_bytes DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "scan_id": row[1],
                "file_name": row[2],
                "file_path": row[3],
                "extension": row[4],
                "size_bytes": row[5],
                "created_at": row[6],
                "modified_at": row[7],
                "accessed_at": row[8],
                "mime_type": row[9],
            }
            for row in rows
        ]

    # ==================================================
    # SAVE DUPLICATE GROUP
    # ==================================================

    def save_duplicate_group(
        self,
        scan_id: int,
        file_hash: str,
        file_count: int,
        total_size_bytes: int,
        duplicate_size_bytes: int,
    ) -> int:
        """
        Save a duplicate group and return its database ID.
        """

        created_at = datetime.now().isoformat()

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO duplicate_groups (
                    scan_id,
                    file_hash,
                    file_count,
                    total_size_bytes,
                    duplicate_size_bytes,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    file_hash,
                    file_count,
                    total_size_bytes,
                    duplicate_size_bytes,
                    created_at,
                ),
            )

            duplicate_group_id = cursor.lastrowid

            connection.commit()

        return duplicate_group_id

    # ==================================================
    # SAVE DUPLICATE FILE
    # ==================================================

    def save_duplicate_file(
        self,
        duplicate_group_id: int,
        file_id: int,
        file_path: str,
        file_size_bytes: int,
    ) -> int:
        """
        Save a file belonging to a duplicate group.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO duplicate_files (
                    duplicate_group_id,
                    file_id,
                    file_path,
                    file_size_bytes
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    duplicate_group_id,
                    file_id,
                    file_path,
                    file_size_bytes,
                ),
            )

            duplicate_file_id = cursor.lastrowid

            connection.commit()

        return duplicate_file_id

    # ==================================================
    # SAVE NEAR-DUPLICATE GROUP
    # ==================================================

    def save_near_duplicate_group(
        self,
        scan_id: int,
        representative_hash: str,
        file_count: int,
        total_size_bytes: int,
        duplicate_size_bytes: int,
        similarity_threshold: int,
    ) -> int:
        """
        Save a near-duplicate group and return its database ID.
        """

        created_at = datetime.now().isoformat()

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO near_duplicate_groups (
                    scan_id,
                    representative_hash,
                    file_count,
                    total_size_bytes,
                    duplicate_size_bytes,
                    similarity_threshold,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    representative_hash,
                    file_count,
                    total_size_bytes,
                    duplicate_size_bytes,
                    similarity_threshold,
                    created_at,
                ),
            )

            near_duplicate_group_id = cursor.lastrowid

            connection.commit()

        return near_duplicate_group_id

    # ==================================================
    # SAVE NEAR-DUPLICATE FILE
    # ==================================================

    def save_near_duplicate_file(
        self,
        near_duplicate_group_id: int,
        file_id: int,
        file_path: str,
        file_size_bytes: int,
        perceptual_hash: str,
    ) -> int:
        """
        Save a file belonging to a near-duplicate group.
        """

        with self.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO near_duplicate_files (
                    near_duplicate_group_id,
                    file_id,
                    file_path,
                    file_size_bytes,
                    perceptual_hash
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    near_duplicate_group_id,
                    file_id,
                    file_path,
                    file_size_bytes,
                    perceptual_hash,
                ),
            )

            near_duplicate_file_id = cursor.lastrowid

            connection.commit()

        return near_duplicate_file_id