import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)

from app.database.database import Database
from app.duplicates.near_duplicate_analytics_service import (
    NearDuplicateAnalyticsService,
)


def main():
    print("=" * 60)
    print("NEAR-DUPLICATE ANALYTICS TEST")
    print("=" * 60)

    database = Database()

    database.initialize()
    database.migrate_scan_statistics()
    database.migrate_duplicate_tables()
    database.migrate_near_duplicate_tables()

    analytics = NearDuplicateAnalyticsService(
        database=database
    )

    # ------------------------------------------------------
    # 1. Create controlled scan
    # ------------------------------------------------------

    scan_id = database.create_scan(
        "near_duplicate_analytics_test"
    )

    print(
        f"\nCreated test scan: {scan_id}"
    )

    try:
        # --------------------------------------------------
        # 2. Create test files
        # --------------------------------------------------

        from app.scanner.metadata import FileMetadata

        file_paths = [
            "analytics_test/image_1.png",
            "analytics_test/image_2.png",
        ]

        file_ids = []

        for file_path in file_paths:

            metadata = FileMetadata(
                file_path=file_path,
                file_name=Path(file_path).name,
                extension=".png",
                mime_type="image/png",
                size_bytes=1500,
                created_at=None,
                modified_at=None,
                accessed_at=None,
            )

            file_id = database.save_file(
                scan_id=scan_id,
                metadata=metadata,
            )

            file_ids.append(file_id)

        # --------------------------------------------------
        # 3. Create test group
        # --------------------------------------------------

        group_id = (
            database.save_near_duplicate_group(
                scan_id=scan_id,
                representative_hash=(
                    "bdb0a336a4637075"
                ),
                file_count=2,
                total_size_bytes=3000,
                duplicate_size_bytes=1500,
                similarity_threshold=8,
            )
        )

        database.save_near_duplicate_file(
            near_duplicate_group_id=group_id,
            file_id=file_ids[0],
            file_path=file_paths[0],
            file_size_bytes=1500,
            perceptual_hash=(
                "bdb0a336a4637075"
            ),
        )

        database.save_near_duplicate_file(
            near_duplicate_group_id=group_id,
            file_id=file_ids[1],
            file_path=file_paths[1],
            file_size_bytes=1500,
            perceptual_hash=(
                "bdb0a336a4637075"
            ),
        )

        print(
            f"Created test group: {group_id}"
        )

        # --------------------------------------------------
        # 4. Test overall summary
        # --------------------------------------------------

        summary = (
            analytics.get_near_duplicate_summary()
        )

        print("\nOVERALL SUMMARY")
        print(summary)

        assert (
            summary[
                "near_duplicate_group_count"
            ] >= 1
        )

        assert (
            summary[
                "near_duplicate_file_count"
            ] >= 2
        )

        assert (
            summary[
                "near_duplicate_storage_bytes"
            ] >= 1500
        )

        # --------------------------------------------------
        # 5. Test scan-specific summary
        # --------------------------------------------------

        scan_summary = (
            analytics
            .get_near_duplicate_summary_by_scan(
                scan_id
            )
        )

        print("\nSCAN SUMMARY")
        print(scan_summary)

        assert (
            scan_summary[
                "near_duplicate_group_count"
            ] == 1
        )

        assert (
            scan_summary[
                "near_duplicate_file_count"
            ] == 2
        )

        assert (
            scan_summary[
                "near_duplicate_storage_bytes"
            ] == 1500
        )

        # --------------------------------------------------
        # 6. Test group query
        # --------------------------------------------------

        groups = (
            analytics.get_near_duplicate_groups(
                scan_id=scan_id
            )
        )

        print("\nGROUPS")

        for group in groups:
            print(group)

        assert len(groups) == 1

        assert groups[0]["id"] == group_id

        assert groups[0]["file_count"] == 2

        assert (
            groups[0][
                "duplicate_size_bytes"
            ]
            == 1500
        )

        assert (
            groups[0][
                "similarity_threshold"
            ]
            == 8
        )

        # --------------------------------------------------
        # 7. Test group files
        # --------------------------------------------------

        group_files = (
            analytics.get_near_duplicate_group_files(
                group_id
            )
        )

        print("\nGROUP FILES")

        for file_record in group_files:
            print(file_record)

        assert len(group_files) == 2

        assert (
            group_files[0]["near_duplicate_group_id"]
            == group_id
        )

        # --------------------------------------------------
        # 8. Test largest groups
        # --------------------------------------------------

        largest_groups = (
            analytics
            .get_largest_near_duplicate_groups(
                limit=5,
                scan_id=scan_id,
            )
        )

        print("\nLARGEST GROUPS")

        for group in largest_groups:
            print(group)

        assert len(largest_groups) == 1

        assert (
            largest_groups[0]["id"]
            == group_id
        )

        # --------------------------------------------------
        # 9. Test invalid limit
        # --------------------------------------------------

        invalid_groups = (
            analytics
            .get_largest_near_duplicate_groups(
                limit=0,
                scan_id=scan_id,
            )
        )

        assert invalid_groups == []

        print(
            "\nAll analytics assertions passed."
        )

    finally:
        # --------------------------------------------------
        # 10. Cleanup
        # --------------------------------------------------

        with database.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM near_duplicate_files
                WHERE near_duplicate_group_id IN (
                    SELECT id
                    FROM near_duplicate_groups
                    WHERE scan_id = ?
                )
                """,
                (scan_id,),
            )

            cursor.execute(
                """
                DELETE FROM near_duplicate_groups
                WHERE scan_id = ?
                """,
                (scan_id,),
            )

            cursor.execute(
                """
                DELETE FROM files
                WHERE scan_id = ?
                """,
                (scan_id,),
            )

            cursor.execute(
                """
                DELETE FROM scans
                WHERE id = ?
                """,
                (scan_id,),
            )

        print(
            "\nTest data cleaned up."
        )

    print("\n" + "=" * 60)
    print(
        "NEAR-DUPLICATE ANALYTICS TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()