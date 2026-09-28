from pathlib import Path

from app.database.database import Database
from app.services.scan_service import ScanService


TEST_DIRECTORY = Path(
    "data/scan_duplicate_integration_test"
)


def create_test_files() -> list[Path]:
    """
    Create two identical test files.
    """

    TEST_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    original = (
        TEST_DIRECTORY / "original.txt"
    )

    copy = (
        TEST_DIRECTORY / "copy.txt"
    )

    content = (
        "Digital Junk AI scan duplicate integration test."
    )

    original.write_text(
        content,
        encoding="utf-8",
    )

    copy.write_text(
        content,
        encoding="utf-8",
    )

    return [
        original,
        copy,
    ]


def cleanup_test_files(
    test_files: list[Path],
):
    """
    Remove temporary test files.
    """

    for file_path in test_files:

        if file_path.exists():
            file_path.unlink()

    if TEST_DIRECTORY.exists():
        TEST_DIRECTORY.rmdir()


def main():
    print("=" * 70)
    print("SCAN + DUPLICATE INTEGRATION TEST")
    print("=" * 70)

    # --------------------------------------------------
    # Create test files
    # --------------------------------------------------

    test_files = create_test_files()

    print(
        f"\nCreated {len(test_files)} test files."
    )

    # --------------------------------------------------
    # Run actual ScanService
    # --------------------------------------------------

    scan_service = ScanService()

    result = scan_service.scan(
        str(TEST_DIRECTORY)
    )

    print("\nSCAN RESULT")
    print("-" * 70)

    print(
        f"Scan ID: {result.scan_id}"
    )

    print(
        f"Files found: {len(test_files)}"
    )

    print(
        f"Files processed: "
        f"{result.successful_count}"
    )

    print(
        f"Files failed: "
        f"{result.failed_count}"
    )

    # --------------------------------------------------
    # Verify scan result
    # --------------------------------------------------

    assert result.scan_id is not None

    assert result.successful_count == 2

    assert result.failed_count == 0

    # --------------------------------------------------
    # Check database
    # --------------------------------------------------

    database = Database()

    database.initialize()
    database.migrate_scan_statistics()
    database.migrate_duplicate_tables()

    with database.get_connection() as connection:

        cursor = connection.cursor()

        # --------------------------------------------------
        # Check scan statistics
        # --------------------------------------------------

        cursor.execute(
            """
            SELECT
                files_found,
                files_processed,
                files_failed,
                total_size_bytes
            FROM scans
            WHERE id = ?
            """,
            (result.scan_id,),
        )

        statistics = cursor.fetchone()

        # --------------------------------------------------
        # Check duplicate groups
        # --------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                file_hash,
                file_count,
                total_size_bytes,
                duplicate_size_bytes
            FROM duplicate_groups
            WHERE scan_id = ?
            """,
            (result.scan_id,),
        )

        duplicate_group = cursor.fetchone()

        # --------------------------------------------------
        # Check duplicate files
        # --------------------------------------------------

        if duplicate_group is not None:

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
                ORDER BY id
                """,
                (duplicate_group[0],),
            )

            duplicate_files = cursor.fetchall()

        else:

            duplicate_files = []

    # --------------------------------------------------
    # Print scan statistics
    # --------------------------------------------------

    print("\nDATABASE SCAN STATISTICS")
    print("-" * 70)

    print(statistics)

    assert statistics is not None

    assert statistics[0] == 2
    assert statistics[1] == 2
    assert statistics[2] == 0

    # --------------------------------------------------
    # Print duplicate results
    # --------------------------------------------------

    print("\nDUPLICATE DETECTION")
    print("-" * 70)

    if duplicate_group is not None:

        print(
            "Duplicate groups: 1"
        )

        print(
            f"Files in group: "
            f"{duplicate_group[2]}"
        )

        print(
            f"Total size: "
            f"{duplicate_group[3]} bytes"
        )

        print(
            f"Duplicate storage: "
            f"{duplicate_group[4]} bytes"
        )

    else:

        print(
            "Duplicate groups: 0"
        )

    # --------------------------------------------------
    # Verify duplicate detection
    # --------------------------------------------------

    assert duplicate_group is not None

    assert duplicate_group[2] == 2

    assert len(duplicate_files) == 2

    # --------------------------------------------------
    # Print duplicate files
    # --------------------------------------------------

    print("\nDUPLICATE FILES")
    print("-" * 70)

    for duplicate_file in duplicate_files:

        print(
            f"{duplicate_file[3]} | "
            f"{duplicate_file[4]} bytes"
        )

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    cleanup_test_files(
        test_files
    )

    print("\n" + "=" * 70)
    print(
        "SUCCESS: ScanService duplicate integration "
        "is working correctly."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()