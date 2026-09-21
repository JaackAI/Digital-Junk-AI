from pathlib import Path

from app.duplicates.duplicate_detector import (
    DuplicateDetector,
)


TEST_DIRECTORY = Path(
    r"C:\Users\AMD\Desktop\Tested"
)


print("=" * 60)
print("Digital Junk AI - Duplicate Detection Test")
print("=" * 60)


# ==================================================
# FIND FILES
# ==================================================

files = [
    path
    for path in TEST_DIRECTORY.rglob("*")
    if path.is_file()
]


print(
    f"\nFiles found: {len(files)}"
)


# ==================================================
# DETECT DUPLICATES
# ==================================================

detector = DuplicateDetector()

duplicate_groups = detector.find_duplicates(
    files
)


# ==================================================
# DISPLAY RESULTS
# ==================================================

print(
    f"\nDuplicate groups: "
    f"{detector.get_duplicate_group_count(duplicate_groups)}"
)

print(
    f"Duplicate files: "
    f"{detector.get_duplicate_file_count(duplicate_groups)}"
)


# ==================================================
# DISPLAY GROUPS
# ==================================================

if duplicate_groups:

    print("\nDuplicate Groups")
    print("-" * 60)

    group_number = 1

    for file_hash, paths in duplicate_groups.items():

        print(
            f"\nGroup #{group_number}"
        )

        print(
            f"SHA-256: {file_hash}"
        )

        for path in paths:

            print(
                f"  → {path}"
            )

        group_number += 1

else:

    print(
        "\nNo exact duplicate files found."
    )


# ==================================================
# STORAGE
# ==================================================

duplicate_storage = (
    detector.get_duplicate_storage_bytes(
        duplicate_groups
    )
)


print(
    f"\nPotential duplicate storage: "
    f"{duplicate_storage:,} bytes"
)


print("\n" + "=" * 60)
print("Duplicate detection test completed.")
print("=" * 60)