from pathlib import Path

from app.database.database import Database
from app.duplicates.duplicate_detector import DuplicateDetector
from app.duplicates.duplicate_storage_service import (
    DuplicateStorageService,
)


TEST_DIRECTORY = Path("data/duplicate_storage_test")


def create_test_files() -> list[Path]:
    """
    Create two identical test files.
    """

    TEST_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    original = TEST_DIRECTORY / "original.txt"
    copy = TEST_DIRECTORY / "copy.txt"

    content = (
        "Digital Junk AI duplicate storage test."
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


def main():
    print("Starting duplicate storage test...")

    database = Database()

    database.initialize()
    database.migrate_scan_statistics()
    database.migrate_duplicate_tables()

    # --------------------------------------------------
    # Create test files
    # --------------------------------------------------

    test_files = create_test_files()

    print(
        f"Created {len(test_files)} test files."
    )

    # --------------------------------------------------
    # Create scan
    # --------------------------------------------------

    scan_id = database.create_scan(
        str(TEST_DIRECTORY)
    )

    print(
        f"Created test scan: {scan_id}"
    )

    # --------------------------------------------------
    # Save file records
    # --------------------------------------------------

    with database.get_connection() as connection:

        cursor = connection.cursor()

        for file_path in test_files:

            cursor.execute(
                """
                INSERT INTO files (
                    scan_id,
                    file_name,
                    file_path,
                    extension,
                    size_bytes
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    file_path.name,
                    str(file_path),
                    file_path.suffix,
                    file_path.stat().st_size,
                ),
            )

        connection.commit()

    print("Test file records saved.")

    # --------------------------------------------------
    # Detect duplicates
    # --------------------------------------------------

    detector = DuplicateDetector()

    duplicate_groups = detector.find_duplicates(
        test_files
    )

    print(
        f"Duplicate groups detected: "
        f"{len(duplicate_groups)}"
    )

    assert len(duplicate_groups) == 1

    # --------------------------------------------------
    # Save duplicate results
    # --------------------------------------------------

    storage_service = DuplicateStorageService(
        database=database
    )

    saved_groups = (
        storage_service.save_duplicate_groups(
            scan_id=scan_id,
            duplicate_groups=duplicate_groups,
        )
    )

    print(
        f"Duplicate groups saved: "
        f"{saved_groups}"
    )

    assert saved_groups == 1

    # --------------------------------------------------
    # Verify duplicate group
    # --------------------------------------------------

    with database.get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                scan_id,
                file_hash,
                file_count,
                total_size_bytes,
                duplicate_size_bytes
            FROM duplicate_groups
            WHERE scan_id = ?
            """,
            (scan_id,),
        )

        group = cursor.fetchone()

    print("\nSaved duplicate group:")
    print(group)

    assert group is not None
    assert group[1] == scan_id
    assert group[3] == 2

    # --------------------------------------------------
    # Verify duplicate files
    # --------------------------------------------------

    with database.get_connection() as connection:

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
            ORDER BY id
            """,
            (group[0],),
        )

        duplicate_files = cursor.fetchall()

    print("\nSaved duplicate files:")

    for duplicate_file in duplicate_files:
        print(duplicate_file)

    assert len(duplicate_files) == 2

    # --------------------------------------------------
    # Cleanup test files
    # --------------------------------------------------

    for file_path in test_files:

        if file_path.exists():
            file_path.unlink()

    if TEST_DIRECTORY.exists():
        TEST_DIRECTORY.rmdir()

    print(
        "\nSUCCESS: DuplicateStorageService "
        "is working correctly."
    )


if __name__ == "__main__":
    main()