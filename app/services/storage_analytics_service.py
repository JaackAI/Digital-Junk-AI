from app.database.database import Database


class StorageAnalyticsService:
    """
    Provides storage analytics for Digital Junk AI.
    """

    def __init__(
        self,
        database: Database | None = None,
    ):
        self.database = database or Database()

        self.database.initialize()
        self.database.migrate_scan_statistics()

    # ==================================================
    # STORAGE SUMMARY
    # ==================================================

    def get_storage_summary(self) -> dict:
        """
        Return overall storage statistics.
        """

        return self.database.get_storage_summary()

    # ==================================================
    # STORAGE BY EXTENSION
    # ==================================================

    def get_storage_by_extension(self) -> list[dict]:
        """
        Return storage statistics grouped by extension.
        """

        return self.database.get_storage_by_extension()

    # ==================================================
    # STORAGE BY CATEGORY
    # ==================================================

    def get_storage_by_category(self) -> list[dict]:
        """
        Return storage statistics grouped by category.
        """

        return self.database.get_storage_by_category()

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

        return self.database.get_largest_files(
            limit=limit
        )

    # ==================================================
    # SCAN HISTORY
    # ==================================================

    def get_scan_history(self) -> list[dict]:
        """
        Return historical scan records.
        """

        return self.database.get_scan_history()

    # ==================================================
    # SCAN DETAILS
    # ==================================================

    def get_scan_by_id(
        self,
        scan_id: int,
    ) -> dict | None:
        """
        Return details for a specific scan.
        """

        return self.database.get_scan_by_id(
            scan_id
        )

    # ==================================================
    # FILES FROM SCAN
    # ==================================================

    def get_files_by_scan(
        self,
        scan_id: int,
    ) -> list[dict]:
        """
        Return files belonging to a specific scan.
        """

        return self.database.get_files_by_scan(
            scan_id
        )

    # ==================================================
    # LATEST SCAN
    # ==================================================

    def get_latest_scan(self) -> dict | None:
        """
        Return the most recent scan.
        """

        return self.database.get_latest_scan()
        # ==================================================
    # LATEST SCAN ANALYTICS
    # ==================================================

    def get_latest_scan_storage_summary(self) -> dict:
        return self.database.get_latest_scan_storage_summary()

    def get_latest_scan_storage_by_category(self) -> list[dict]:
        return self.database.get_latest_scan_storage_by_category()

    def get_latest_scan_largest_files(
        self,
        limit: int = 10,
    ) -> list[dict]:
        return self.database.get_latest_scan_largest_files(
            limit=limit
        )