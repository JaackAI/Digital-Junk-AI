import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)

from app.database.database import Database
from app.duplicates.near_duplicate_detector import (
    NearDuplicateDetector,
)
from app.duplicates.near_duplicate_storage_service import (
    NearDuplicateStorageService,
)
from app.scanner.metadata import MetadataExtractor


TEST_DIRECTORY = Path(
    r"C:\Users\AMD\Desktop\Tested"
)


def main():
    print("=" * 60)
    print("NEAR-DUPLICATE STORAGE SERVICE TEST")
    print("=" * 60)

    database = Database()

    database.initialize()
    database.migrate_scan_statistics()
    database.migrate_duplicate_tables()
    database.migrate_near_duplicate_tables()

    if not TEST_DIRECTORY.exists():
        raise FileNotFoundError(
            f"Test directory does not exist: "
            f"{TEST_DIRECTORY}"
        )

    # ------------------------------------------------------
    # 1. Find supported images
    # ------------------------------------------------------

    supported_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    image_paths = [
        path
        for path in TEST_DIRECTORY.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in supported_extensions
        )
    ]

    print(
        f"\nImages found: {len(image_paths)}"
    )

    if len(image_paths) == 0:
        print(
            "\nNo supported images found."
        )
        return

    for path in image_paths:
        print(f"  {path.name}")

    # ------------------------------------------------------
    # 2. Create a temporary near-duplicate
    # ------------------------------------------------------

    original = image_paths[0]

    temporary_image = (
        TEST_DIRECTORY
        / "near_duplicate_storage_test.png"
    )

    try:
        from PIL import Image

        with Image.open(original) as image:

            new_width = int(
                image.width * 0.95
            )

            new_height = int(
                image.height * 0.95
            )

            modified = image.resize(
                (
                    new_width,
                    new_height,
                )
            )

            modified.save(
                temporary_image,
                format="PNG",
            )

        print(
            "\nTemporary near-duplicate created:"
        )
        print(
            f"  {temporary_image.name}"
        )

        # --------------------------------------------------
        # 3. Detect near duplicates
        # --------------------------------------------------

        detector = NearDuplicateDetector(
            similarity_threshold=8
        )

        test_paths = [
            original,
            temporary_image,
        ]

        near_duplicate_groups = (
            detector.find_near_duplicates(
                test_paths
            )
        )

        print(
            "\nNEAR-DUPLICATE DETECTION"
        )

        print(
            f"Groups found: "
            f"{len(near_duplicate_groups)}"
        )

        assert len(near_duplicate_groups) >= 1

        for representative_hash, paths in (
            near_duplicate_groups.items()
        ):
            print(
                f"\nRepresentative hash: "
                f"{representative_hash}"
            )

            for path in paths:
                print(
                    f"  {path.name}"
                )

        # --------------------------------------------------
        # 4. Create database scan
        # --------------------------------------------------

        scan_id = database.create_scan(
            str(TEST_DIRECTORY)
        )

        print(
            f"\nCreated test scan: {scan_id}"
        )

        # --------------------------------------------------
        # 5. Save file metadata
        # --------------------------------------------------

        metadata_extractor = (
            MetadataExtractor()
        )

        file_ids = {}

        for path in test_paths:

            metadata = (
                metadata_extractor.extract(
                    path
                )
            )

            file_id = database.save_file(
                scan_id=scan_id,
                metadata=metadata,
            )

            file_ids[
                str(path.resolve())
            ] = file_id

        print(
            "\nFile metadata saved."
        )

        # --------------------------------------------------
        # 6. Store near-duplicate results
        # --------------------------------------------------

        storage_service = (
            NearDuplicateStorageService(
                database=database
            )
        )

        saved_groups = (
            storage_service
            .save_near_duplicate_groups(
                scan_id=scan_id,
                near_duplicate_groups=(
                    near_duplicate_groups
                ),
                similarity_threshold=8,
            )
        )

        print(
            "\nNEAR-DUPLICATE STORAGE"
        )

        print(
            f"Groups saved: {saved_groups}"
        )

        assert saved_groups >= 1

        # --------------------------------------------------
        # 7. Verify database records
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

            groups = cursor.fetchall()

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

            files = cursor.fetchall()

        print(
            "\nDATABASE GROUPS"
        )

        for group in groups:
            print(group)

        print(
            "\nDATABASE FILES"
        )

        for file_record in files:
            print(file_record)

        # --------------------------------------------------
        # 8. Validate results
        # --------------------------------------------------

        assert len(groups) >= 1

        assert len(files) >= 2

        group = groups[0]

        assert group[1] == scan_id

        assert group[3] == 2

        assert group[6] == 8

        print(
            "\nAll storage assertions passed."
        )

        # --------------------------------------------------
        # 9. Cleanup database records
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
            "\nDatabase test data cleaned up."
        )

    finally:
        # --------------------------------------------------
        # 10. Remove temporary image
        # --------------------------------------------------

        if temporary_image.exists():
            temporary_image.unlink()

            print(
                "Temporary image removed."
            )

    print("\n" + "=" * 60)
    print(
        "NEAR-DUPLICATE STORAGE SERVICE TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()