from app.database.database import Database


class DuplicateAnalyticsService:
    """
    Provides analytics and query operations for
    exact duplicate files.
    """

    def __init__(
        self,
        database: Database | None = None,
    ):
        self.database = database or Database()

        self.database.initialize()
        self.database.migrate_scan_statistics()
        self.database.migrate_duplicate_tables()

    def get_duplicate_summary(self) -> dict:
        """
        Return overall duplicate statistics.

        Returns:
            Dictionary containing:
            - duplicate_group_count
            - duplicate_file_count
            - duplicate_storage_bytes
        """

        with self.database.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS duplicate_group_count,
                    COALESCE(
                        SUM(file_count),
                        0
                    ) AS duplicate_file_count,
                    COALESCE(
                        SUM(duplicate_size_bytes),
                        0
                    ) AS duplicate_storage_bytes
                FROM duplicate_groups
                """
            )

            row = cursor.fetchone()

        return {
            "duplicate_group_count": row[0],
            "duplicate_file_count": row[1],
            "duplicate_storage_bytes": row[2],
        }

    def get_duplicate_summary_by_scan(
        self,
        scan_id: int,
    ) -> dict:
        """
        Return duplicate statistics for a specific scan.
        """

        with self.database.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS duplicate_group_count,
                    COALESCE(
                        SUM(file_count),
                        0
                    ) AS duplicate_file_count,
                    COALESCE(
                        SUM(duplicate_size_bytes),
                        0
                    ) AS duplicate_storage_bytes
                FROM duplicate_groups
                WHERE scan_id = ?
                """,
                (scan_id,),
            )

            row = cursor.fetchone()

        return {
            "duplicate_group_count": row[0],
            "duplicate_file_count": row[1],
            "duplicate_storage_bytes": row[2],
        }

    def get_duplicate_groups(
        self,
        scan_id: int | None = None,
    ) -> list[dict]:
        """
        Return duplicate groups.

        If scan_id is provided, only groups from that
        scan are returned.
        """

        with self.database.get_connection() as connection:

            cursor = connection.cursor()

            if scan_id is None:

                cursor.execute(
                    """
                    SELECT
                        id,
                        scan_id,
                        file_hash,
                        file_count,
                        total_size_bytes,
                        duplicate_size_bytes,
                        created_at
                    FROM duplicate_groups
                    ORDER BY duplicate_size_bytes DESC
                    """
                )

            else:

                cursor.execute(
                    """
                    SELECT
                        id,
                        scan_id,
                        file_hash,
                        file_count,
                        total_size_bytes,
                        duplicate_size_bytes,
                        created_at
                    FROM duplicate_groups
                    WHERE scan_id = ?
                    ORDER BY duplicate_size_bytes DESC
                    """,
                    (scan_id,),
                )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "scan_id": row[1],
                "file_hash": row[2],
                "file_count": row[3],
                "total_size_bytes": row[4],
                "duplicate_size_bytes": row[5],
                "created_at": row[6],
            }
            for row in rows
        ]

    def get_duplicate_group_files(
        self,
        duplicate_group_id: int,
    ) -> list[dict]:
        """
        Return all files belonging to a duplicate group.
        """

        with self.database.get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    duplicate_group_id,
                    file_id,
                    file_path,
                    file_size_bytes
                FROM duplicate_files
                WHERE duplicate_group_id = ?
                ORDER BY file_path
                """,
                (duplicate_group_id,),
            )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "duplicate_group_id": row[1],
                "file_id": row[2],
                "file_path": row[3],
                "file_size_bytes": row[4],
            }
            for row in rows
        ]

    def get_largest_duplicate_groups(
        self,
        limit: int = 10,
        scan_id: int | None = None,
    ) -> list[dict]:
        """
        Return the duplicate groups using the most
        recoverable storage.

        Args:
            limit: Maximum number of groups to return.
            scan_id: Optional scan filter.
        """

        if limit <= 0:
            return []

        with self.database.get_connection() as connection:

            cursor = connection.cursor()

            if scan_id is None:

                cursor.execute(
                    """
                    SELECT
                        id,
                        scan_id,
                        file_hash,
                        file_count,
                        total_size_bytes,
                        duplicate_size_bytes,
                        created_at
                    FROM duplicate_groups
                    ORDER BY duplicate_size_bytes DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            else:

                cursor.execute(
                    """
                    SELECT
                        id,
                        scan_id,
                        file_hash,
                        file_count,
                        total_size_bytes,
                        duplicate_size_bytes,
                        created_at
                    FROM duplicate_groups
                    WHERE scan_id = ?
                    ORDER BY duplicate_size_bytes DESC
                    LIMIT ?
                    """,
                    (scan_id, limit),
                )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "scan_id": row[1],
                "file_hash": row[2],
                "file_count": row[3],
                "total_size_bytes": row[4],
                "duplicate_size_bytes": row[5],
                "created_at": row[6],
            }
            for row in rows
        ]