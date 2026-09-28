from pathlib import Path

from app.database.database import Database


def main():
    database = Database()

    # Make sure all required tables exist.
    database.initialize()
    database.migrate_scan_statistics()
    database.migrate_duplicate_tables()

    print("Database initialized successfully.")

    # --------------------------------------------------
    # Create a test scan
    # --------------------------------------------------

    scan_id = database.create_scan(
        "data/duplicate_database_test"
    )

    print(f"Created test scan: {scan_id}")

    # --------------------------------------------------
    # Create test file records
    # --------------------------------------------------

    file_1_id = database.get_connection()

    with database.get_connection() as connection:
        cursor = connection.cursor()

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
                "original.txt",
                "data/duplicate_database_test/original.txt",
                ".txt",
                100,
            ),
        )

        file_1_id = cursor.lastrowid

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
                "copy.txt",
                "data/duplicate_database_test/copy.txt",
                ".txt",
                100,
            ),
        )

        file_2_id = cursor.lastrowid

        connection.commit()

    print(
        f"Created test files: "
        f"{file_1_id}, {file_2_id}"
    )

    # --------------------------------------------------
    # Save duplicate group
    # --------------------------------------------------

    test_hash = (
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    )

    duplicate_group_id = database.save_duplicate_group(
        scan_id=scan_id,
        file_hash=test_hash,
        file_count=2,
        total_size_bytes=200,
        duplicate_size_bytes=100,
    )

    print(
        f"Created duplicate group: "
        f"{duplicate_group_id}"
    )

    # --------------------------------------------------
    # Save duplicate files
    # --------------------------------------------------

    duplicate_file_1_id = (
        database.save_duplicate_file(
            duplicate_group_id=duplicate_group_id,
            file_id=file_1_id,
            file_path=(
                "data/duplicate_database_test/"
                "original.txt"
            ),
            file_size_bytes=100,
        )
    )

    duplicate_file_2_id = (
        database.save_duplicate_file(
            duplicate_group_id=duplicate_group_id,
            file_id=file_2_id,
            file_path=(
                "data/duplicate_database_test/"
                "copy.txt"
            ),
            file_size_bytes=100,
        )
    )

    print(
        f"Created duplicate file records: "
        f"{duplicate_file_1_id}, "
        f"{duplicate_file_2_id}"
    )

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
            WHERE id = ?
            """,
            (duplicate_group_id,),
        )

        group = cursor.fetchone()

    print("\nDuplicate group:")
    print(group)

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
            (duplicate_group_id,),
        )

        duplicate_files = cursor.fetchall()

    print("\nDuplicate files:")

    for duplicate_file in duplicate_files:
        print(duplicate_file)

    # --------------------------------------------------
    # Validate results
    # --------------------------------------------------

    assert group is not None

    assert group[0] == duplicate_group_id
    assert group[1] == scan_id
    assert group[2] == test_hash
    assert group[3] == 2
    assert group[4] == 200
    assert group[5] == 100

    assert len(duplicate_files) == 2

    print(
        "\nSUCCESS: Duplicate database "
        "storage is working correctly."
    )


if __name__ == "__main__":
    main()