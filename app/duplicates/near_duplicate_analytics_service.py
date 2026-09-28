from app.database.database import Database


class NearDuplicateAnalyticsService:
    """
    Provides analytics and query operations for
    near-duplicate image files.
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

    def get_near_duplicate_summary(self) -> dict:
        """
        Return overall near-duplicate statistics.

        Returns:
            Dictionary containing:
            - near_duplicate_group_count
            - near_duplicate_file_count
            - near_duplicate_storage_bytes
        """

        with self.database.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS near_duplicate_group_count,
                    COALESCE(
                        SUM(file_count),
                        0
                    ) AS near_duplicate_file_count,
                    COALESCE(
                        SUM(duplicate_size_bytes),
                        0
                    ) AS near_duplicate_storage_bytes
                FROM near_duplicate_groups
                """
            )

            row = cursor.fetchone()

        return {
            "near_duplicate_group_count": row[0],
            "near_duplicate_file_count": row[1],
            "near_duplicate_storage_bytes": row[2],
        }

    def get_near_duplicate_summary_by_scan(
        self,
        scan_id: int,
    ) -> dict:
        """
        Return near-duplicate statistics for
        a specific scan.
        """

        with self.database.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS near_duplicate_group_count,
                    COALESCE(
                        SUM(file_count),
                        0
                    ) AS near_duplicate_file_count,
                    COALESCE(
                        SUM(duplicate_size_bytes),
                        0
                    ) AS near_duplicate_storage_bytes
                FROM near_duplicate_groups
                WHERE scan_id = ?
                """,
                (scan_id,),
            )

            row = cursor.fetchone()

        return {
            "near_duplicate_group_count": row[0],
            "near_duplicate_file_count": row[1],
            "near_duplicate_storage_bytes": row[2],
        }

    def get_near_duplicate_groups(
        self,
        scan_id: int | None = None,
    ) -> list[dict]:
        """
        Return near-duplicate groups.

        If scan_id is provided, only groups from
        that scan are returned.
        """

        with self.database.get_connection() as connection:
            cursor = connection.cursor()

            if scan_id is None:
                cursor.execute(
                    """
                    SELECT
                        id,
                        scan_id,
                        representative_hash,
                        file_count,
                        total_size_bytes,
                        duplicate_size_bytes,
                        similarity_threshold,
                        created_at
                    FROM near_duplicate_groups
                    ORDER BY duplicate_size_bytes DESC
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        id,
                        scan_id,
                        representative_hash,
                        file_count,
                        total_size_bytes,
                        duplicate_size_bytes,
                        similarity_threshold,
                        created_at
                    FROM near_duplicate_groups
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
                "representative_hash": row[2],
                "file_count": row[3],
                "total_size_bytes": row[4],
                "duplicate_size_bytes": row[5],
                "similarity_threshold": row[6],
                "created_at": row[7],
            }
            for row in rows
        ]

    def get_near_duplicate_group_files(
        self,
        near_duplicate_group_id: int,
    ) -> list[dict]:
        """
        Return all files belonging to a
        near-duplicate group.
        """

        with self.database.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    near_duplicate_group_id,
                    file_id,
                    file_path,
                    file_size_bytes,
                    perceptual_hash
                FROM near_duplicate_files
                WHERE near_duplicate_group_id = ?
                ORDER BY file_path
                """,
                (near_duplicate_group_id,),
            )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "near_duplicate_group_id": row[1],
                "file_id": row[2],
                "file_path": row[3],
                "file_size_bytes": row[4],
                "perceptual_hash": row[5],
            }
            for row in rows
        ]

    def get_largest_near_duplicate_groups(
        self,
        limit: int = 10,
        scan_id: int | None = None,
    ) -> list[dict]:
        """
        Return near-duplicate groups using the most
        recoverable storage.

        Args:
            limit:
                Maximum number of groups to return.

            scan_id:
                Optional scan filter.
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
                        representative_hash,
                        file_count,
                        total_size_bytes,
                        duplicate_size_bytes,
                        similarity_threshold,
                        created_at
                    FROM near_duplicate_groups
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
                        representative_hash,
                        file_count,
                        total_size_bytes,
                        duplicate_size_bytes,
                        similarity_threshold,
                        created_at
                    FROM near_duplicate_groups
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
                "representative_hash": row[2],
                "file_count": row[3],
                "total_size_bytes": row[4],
                "duplicate_size_bytes": row[5],
                "similarity_threshold": row[6],
                "created_at": row[7],
            }
            for row in rows
        ]