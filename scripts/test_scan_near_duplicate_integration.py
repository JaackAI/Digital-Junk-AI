import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)

from PIL import Image

from app.database.database import Database
from app.services.scan_service import ScanService


TEST_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "scan_near_duplicate_integration_test"
)


def create_test_images():
    TEST_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_path = (
        TEST_DIRECTORY / "original.png"
    )

    near_duplicate_path = (
        TEST_DIRECTORY
        / "near_duplicate.png"
    )

    image = Image.new(
        "RGB",
        (300, 200),
        "white",
    )

    image.save(
        original_path,
        format="PNG",
    )

    modified = image.resize(
        (285, 190)
    )

    modified.save(
        near_duplicate_path,
        format="PNG",
    )

    return (
        original_path,
        near_duplicate_path,
    )


def main():
    print("=" * 60)
    print("SCAN + NEAR-DUPLICATE INTEGRATION TEST")
    print("=" * 60)

    database = Database()

    database.initialize()
    database.migrate_scan_statistics()
    database.migrate_duplicate_tables()
    database.migrate_near_duplicate_tables()

    original_path = None
    near_duplicate_path = None
    scan_id = None

    try:
        # --------------------------------------------------
        # 1. Create controlled images
        # --------------------------------------------------

        (
            original_path,
            near_duplicate_path,
        ) = create_test_images()

        print("\nTEST FILES")

        print(
            f"  {original_path.name}"
        )

        print(
            f"  {near_duplicate_path.name}"
        )

        # --------------------------------------------------
        # 2. Run real ScanService
        # --------------------------------------------------

        scan_service = ScanService(
            database=database
        )

        result = scan_service.scan(
            str(TEST_DIRECTORY)
        )

        scan_id = result.scan_id

        print("\nSCAN RESULT")

        print(
            f"Scan ID: {scan_id}"
        )

        print(
            f"Files found: "
            f"{len(result.files) + result.failed_count}"
        )

        print(
            f"Files processed: "
            f"{result.successful_count}"
        )

        print(
            f"Files failed: "
            f"{result.failed_count}"
        )

        assert scan_id is not None

        assert result.successful_count == 2

        assert result.failed_count == 0

        # --------------------------------------------------
        # 3. Verify scan statistics
        # --------------------------------------------------

        with database.get_connection() as connection:
            cursor = connection.cursor()

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
                (scan_id,),
            )

            scan_statistics = (
                cursor.fetchone()
            )

        print("\nDATABASE SCAN STATISTICS")

        print(scan_statistics)

        assert scan_statistics is not None

        assert scan_statistics[0] == 2

        assert scan_statistics[1] == 2

        assert scan_statistics[2] == 0

        # --------------------------------------------------
        # 4. Verify exact duplicates
        # --------------------------------------------------

        with database.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(*)
                FROM duplicate_groups
                WHERE scan_id = ?
                """,
                (scan_id,),
            )

            exact_duplicate_group_count = (
                cursor.fetchone()[0]
            )

        print("\nEXACT DUPLICATES")

        print(
            f"Duplicate groups: "
            f"{exact_duplicate_group_count}"
        )

        # The two generated images are visually
        # similar but have different binary data.
        assert exact_duplicate_group_count == 0

        # --------------------------------------------------
        # 5. Verify near duplicates
        # --------------------------------------------------

        with database.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    scan_id,
                    representative_hash,
                    file_count,
                    total_size_bytes,
                    duplicate_size_bytes,
                    similarity_threshold
                FROM near_duplicate_groups
                WHERE scan_id = ?
                """,
                (scan_id,),
            )

            near_duplicate_groups = (
                cursor.fetchall()
            )

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
                WHERE near_duplicate_group_id IN (
                    SELECT id
                    FROM near_duplicate_groups
                    WHERE scan_id = ?
                )
                ORDER BY id
                """,
                (scan_id,),
            )

            near_duplicate_files = (
                cursor.fetchall()
            )

        print("\nNEAR DUPLICATES")

        print(
            f"Near-duplicate groups: "
            f"{len(near_duplicate_groups)}"
        )

        print(
            f"Near-duplicate files: "
            f"{len(near_duplicate_files)}"
        )

        for group in near_duplicate_groups:
            print(
                f"\nGroup ID: {group[0]}"
            )

            print(
                f"File count: {group[3]}"
            )

            print(
                f"Total size: "
                f"{group[4]} bytes"
            )

            print(
                f"Duplicate storage: "
                f"{group[5]} bytes"
            )

            print(
                f"Threshold: {group[6]}"
            )

        for file_record in near_duplicate_files:
            print(
                f"\n  {file_record[3]}"
            )

        # --------------------------------------------------
        # 6. Assertions
        # --------------------------------------------------

        assert len(near_duplicate_groups) == 1

        group = near_duplicate_groups[0]

        assert group[1] == scan_id

        assert group[3] == 2

        assert group[6] == 8

        assert len(near_duplicate_files) == 2

        print(
            "\nAll integration assertions passed."
        )

    finally:
        # --------------------------------------------------
        # 7. Cleanup database
        # --------------------------------------------------

        if scan_id is not None:

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
                    DELETE FROM duplicate_files
                    WHERE duplicate_group_id IN (
                        SELECT id
                        FROM duplicate_groups
                        WHERE scan_id = ?
                    )
                    """,
                    (scan_id,),
                )

                cursor.execute(
                    """
                    DELETE FROM duplicate_groups
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

        # --------------------------------------------------
        # 8. Cleanup test directory
        # --------------------------------------------------

        if (
            original_path is not None
            and original_path.exists()
        ):
            original_path.unlink()

        if (
            near_duplicate_path is not None
            and near_duplicate_path.exists()
        ):
            near_duplicate_path.unlink()

        if (
            TEST_DIRECTORY.exists()
            and not any(TEST_DIRECTORY.iterdir())
        ):
            TEST_DIRECTORY.rmdir()

        print("\nTest data cleaned up.")

    print("\n" + "=" * 60)
    print(
        "SCAN + NEAR-DUPLICATE INTEGRATION TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()