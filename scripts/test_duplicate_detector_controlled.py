from pathlib import Path

from app.duplicates.duplicate_detector import (
    DuplicateDetector,
)


TEST_DIRECTORY = Path(
    "data/duplicate_test"
)


FILE_A = TEST_DIRECTORY / "original.txt"
FILE_B = TEST_DIRECTORY / "copy.txt"


print("=" * 60)
print("Digital Junk AI - Controlled Duplicate Test")
print("=" * 60)


try:

    # ==================================================
    # 1. CREATE TEST DIRECTORY
    # ==================================================

    TEST_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ==================================================
    # 2. CREATE TWO IDENTICAL FILES
    # ==================================================

    test_content = (
        "Digital Junk AI duplicate detection test."
    )

    FILE_A.write_text(
        test_content,
        encoding="utf-8",
    )

    FILE_B.write_text(
        test_content,
        encoding="utf-8",
    )

    print("\nCreated test files:")

    print(
        f"  → {FILE_A}"
    )

    print(
        f"  → {FILE_B}"
    )

    # ==================================================
    # 3. RUN DUPLICATE DETECTION
    # ==================================================

    detector = DuplicateDetector()

    duplicate_groups = detector.find_duplicates(
        [
            FILE_A,
            FILE_B,
        ]
    )

    # ==================================================
    # 4. DISPLAY RESULTS
    # ==================================================

    group_count = (
        detector.get_duplicate_group_count(
            duplicate_groups
        )
    )

    duplicate_file_count = (
        detector.get_duplicate_file_count(
            duplicate_groups
        )
    )

    duplicate_storage = (
        detector.get_duplicate_storage_bytes(
            duplicate_groups
        )
    )

    print(
        f"\nDuplicate groups: {group_count}"
    )

    print(
        f"Duplicate files: {duplicate_file_count}"
    )

    print(
        f"Potential duplicate storage: "
        f"{duplicate_storage} bytes"
    )

    # ==================================================
    # 5. VERIFY EXPECTED RESULT
    # ==================================================

    if group_count == 1:

        print(
            "\n✅ Duplicate detection PASSED."
        )

    else:

        print(
            "\n❌ Duplicate detection FAILED."
        )

finally:

    # ==================================================
    # 6. CLEAN UP
    # ==================================================

    if FILE_A.exists():
        FILE_A.unlink()

    if FILE_B.exists():
        FILE_B.unlink()

    if TEST_DIRECTORY.exists():
        try:
            TEST_DIRECTORY.rmdir()
        except OSError:
            pass

    print(
        "\nTemporary test files removed."
    )

    print(
        "Controlled duplicate test completed."
    )