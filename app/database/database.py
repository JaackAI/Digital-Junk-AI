import sqlite3
from pathlib import Path
from datetime import datetime

from app.scanner.metadata import FileMetadata


class Database:
    def __init__(self, db_path: str = "data/digital_junk_ai.db"):
        self.db_path = Path(db_path)

    def get_connection(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")

        return connection

    def initialize(self) -> None:
        with self.get_connection() as connection:
            cursor = connection.cursor()

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

    def migrate_scan_statistics(self) -> None:
        """
        Adds scan statistics columns to existing databases.

        This is required because CREATE TABLE IF NOT EXISTS
        does not modify an already-existing table.
        """

        columns = {
            "files_found": "INTEGER NOT NULL DEFAULT 0",
            "files_processed": "INTEGER NOT NULL DEFAULT 0",
            "files_failed": "INTEGER NOT NULL DEFAULT 0",
            "total_size_bytes": "INTEGER NOT NULL DEFAULT 0",
        }

        with self.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute("PRAGMA table_info(scans)")

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

    def create_scan(self, directory_path: str) -> int:
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

    def save_file(
        self,
        scan_id: int,
        metadata: FileMetadata,
    ) -> None:
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

    def update_scan_statistics(
        self,
        scan_id: int,
        files_found: int,
        files_processed: int,
        files_failed: int,
        total_size_bytes: int,
    ) -> None:
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

    def complete_scan(self, scan_id: int) -> None:
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