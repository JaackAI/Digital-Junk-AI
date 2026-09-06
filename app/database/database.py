import sqlite3
from pathlib import Path
from datetime import datetime

from app.scanner.metadata import FileMetadata


class Database:
    def __init__(self, db_path: str = "data/digital_junk_ai.db"):
        self.db_path = Path(db_path)

    def get_connection(self):
        """
        Create and return a SQLite database connection.
        """

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection = sqlite3.connect(self.db_path)

        # Enable foreign key support
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    # ==================================================
    # DATABASE INITIALIZATION
    # ==================================================

    def initialize(self) -> None:
        """
        Create database tables if they do not already exist.
        """

        with self.get_connection() as connection:
            cursor = connection.cursor()

            # ------------------------------------------
            # Scans table
            # ------------------------------------------

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

            # ------------------------------------------
            # Files table
            # ------------------------------------------

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

    # ==================================================
    # DATABASE MIGRATION
    # ==================================================

    def migrate_scan_statistics(self) -> None:
        """
        Add scan statistics columns to an existing database.

        CREATE TABLE IF NOT EXISTS does not modify an
        existing table, so this migration ensures older
        databases receive the new columns.
        """

        columns = {
            "files_found": "INTEGER NOT NULL DEFAULT 0",
            "files_processed": "INTEGER NOT NULL DEFAULT 0",
            "files_failed": "INTEGER NOT NULL DEFAULT 0",
            "total_size_bytes": "INTEGER NOT NULL DEFAULT 0",
        }

        with self.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                "PRAGMA table_info(scans)"
            )

            existing_columns = {
                column[1]
                for column in cursor.fetchall()
            }

            for column_name, column_definition in columns.items():

                if column_name not in existing_columns:

                    cursor.execute(
                        f"""
                        ALTER TABLE scans
                        ADD COLUMN {column_name}
                        {column_definition}
                        """
                    )

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

            return cursor.lastrowid

    # ==================================================
    # SAVE FILE
    # ==================================================

    def save_file(
        self,
        scan_id: int,
        metadata: FileMetadata,
    ) -> None:
        """
        Save metadata for a successfully processed file.
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

                    metadata.created_at.isoformat()
                    if metadata.created_at
                    else None,

                    metadata.modified_at.isoformat()
                    if metadata.modified_at
                    else None,

                    metadata.accessed_at.isoformat()
                    if metadata.accessed_at
                    else None,

                    metadata.mime_type,
                ),
            )

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
        Update statistics for a completed scan.
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

    # ==================================================
    # GET SCAN HISTORY
    # ==================================================

    def get_scan_history(self) -> list[dict]:
        """
        Return all previous scans.

        Scans are ordered from newest to oldest.
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
        Return a single scan using its ID.

        Returns:
            Scan dictionary or None if not found.
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
        Return all files belonging to a specific scan.
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
    # GET LATEST SCAN
    # ==================================================

    def get_latest_scan(self) -> dict | None:
        """
        Return the most recent scan.

        Returns:
            Latest scan dictionary or None if no scans exist.
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