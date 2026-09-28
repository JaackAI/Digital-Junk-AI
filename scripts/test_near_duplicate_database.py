import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)

from app.database.database import Database
from app.scanner.metadata import FileMetadata


def main():
    print("=" * 60)
    print("NEAR-DUPLICATE DATABASE TEST")
    print("=" * 60)

    database = Database()

    database.initialize()
    database.migrate_scan_statistics()
    database.migrate_duplicate_tables()
    database.migrate_near_duplicate_tables()

    print("\nDatabase migrations completed.")

    # ------------------------------------------------------
    # 1. Verify tables
    # ------------------------------------------------------

    with database.get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name IN (
                'near_duplicate_groups',
                'near_duplicate_files'
            )
            ORDER BY name
            """
        )

        tables = cursor.fetchall()

    print("\nNEAR-DUPLICATE TABLES")

    for table in tables:
        print(f"  {table[0]}")

    assert len(tables) == 2

    # ------------------------------------------------------
    # 2. Create controlled scan
    # ------------------------------------------------------

    scan_id = database.create_scan(
        "near_duplicate_database_test"
    )

    print(f"\nCreated test scan: {scan_id}")

    try:
        # --------------------------------------------------
        # 3. Insert controlled files
        # --------------------------------------------------

        file_paths = [
            "near_duplicate_test/image_1.png",
            "near_duplicate_test/image_2.png",
        ]

        file_ids = []

        for file_path in file_paths:

            metadata = FileMetadata(
                file_path=file_path,
                file_name=Path(file_path).name,
                extension=".png",
                mime_type="image/png",
                size_bytes=1000,
                created_at=None,
                modified_at=None,
                accessed_at=None,
            )

            file_id = database.save_file(
                scan_id=scan_id,
                metadata=metadata,
            )

            file_ids.append(file_id)

        print("\nCreated test files:")

        for file_id, file_path in zip(
            file_ids,
            file_paths,
        ):
            print(
                f"  File ID {file_id}: {file_path}"
            )

        # --------------------------------------------------
        # 4. Create near-duplicate group
        # --------------------------------------------------

        representative_hash = (
            "bdb0a336a4637075"
        )

        group_id = (
            database.save_near_duplicate_group(
                scan_id=scan_id,
                representative_hash=(
                    representative_hash
                ),
                file_count=2,
                total_size_bytes=2000,
                duplicate_size_bytes=1000,
                similarity_threshold=8,
            )
        )

        print(
            f"\nCreated near-duplicate group: "
            f"{group_id}"
        )

        # --------------------------------------------------
        # 5. Add files to group
        # --------------------------------------------------

        database.save_near_duplicate_file(
            near_duplicate_group_id=group_id,
            file_id=file_ids[0],
            file_path=file_paths[0],
            file_size_bytes=1000,
            perceptual_hash=(
                "bdb0a336a4637075"
            ),
        )

        database.save_near_duplicate_file(
            near_duplicate_group_id=group_id,
            file_id=file_ids[1],
            file_path=file_paths[1],
            file_size_bytes=1000,
            perceptual_hash=(
                "bdb0a336a4637075"
            ),
        )

        print(
            "Added files to near-duplicate group."
        )

        # --------------------------------------------------
        # 6. Verify stored data
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
                WHERE id = ?
                """,
                (group_id,),
            )

            group = cursor.fetchone()

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
                ORDER BY id
                """,
                (group_id,),
            )

            files = cursor.fetchall()

        print("\nSTORED GROUP")
        print(group)

        print("\nSTORED FILES")

        for file_record in files:
            print(file_record)

        # --------------------------------------------------
        # 7. Assertions
        # --------------------------------------------------

        assert group is not None
        assert group[1] == scan_id
        assert group[2] == representative_hash
        assert group[3] == 2
        assert group[4] == 2000
        assert group[5] == 1000
        assert group[6] == 8

        assert len(files) == 2

        assert files[0][2] == file_ids[0]
        assert files[1][2] == file_ids[1]

        assert files[0][3] == file_paths[0]
        assert files[1][3] == file_paths[1]

        assert files[0][4] == 1000
        assert files[1][4] == 1000

        assert files[0][5] == (
            "bdb0a336a4637075"
        )

        assert files[1][5] == (
            "bdb0a336a4637075"
        )

        print("\nAll database assertions passed.")

    finally:
        # --------------------------------------------------
        # 8. Cleanup
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

        print("\nTest data cleaned up.")

    print("\n" + "=" * 60)
    print("NEAR-DUPLICATE DATABASE TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()