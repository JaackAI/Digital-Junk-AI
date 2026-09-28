import sys
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)


from app.duplicates.near_duplicate_detector import (
    NearDuplicateDetector,
)


TEST_DIRECTORY = Path(
    r"C:\Users\AMD\Desktop\Tested"
)

ORIGINAL_IMAGE = (
    TEST_DIRECTORY / "Archietecture.png"
)

TEST_IMAGE = (
    TEST_DIRECTORY / "Archietecture_near_duplicate.png"
)


def main():

    detector = NearDuplicateDetector(
        similarity_threshold=8
    )

    print("=" * 60)
    print("NEAR-DUPLICATE DETECTOR TEST")
    print("=" * 60)

    if not ORIGINAL_IMAGE.exists():

        print(
            f"Original image not found: "
            f"{ORIGINAL_IMAGE}"
        )

        return

    # --------------------------------------------------
    # CREATE CONTROLLED NEAR-DUPLICATE
    # --------------------------------------------------

    with Image.open(ORIGINAL_IMAGE) as image:

        image = image.convert("RGB")

        original_width, original_height = (
            image.size
        )

        new_width = max(
            1,
            int(original_width * 0.95),
        )

        new_height = max(
            1,
            int(original_height * 0.95),
        )

        resized_image = image.resize(
            (new_width, new_height)
        )

        resized_image.save(
            TEST_IMAGE,
            quality=90,
        )

    print(
        f"Original image: "
        f"{ORIGINAL_IMAGE.name}"
    )

    print(
        f"Near-duplicate image: "
        f"{TEST_IMAGE.name}"
    )

    # --------------------------------------------------
    # RUN DETECTOR
    # --------------------------------------------------

    file_paths = [
        ORIGINAL_IMAGE,
        TEST_IMAGE,
    ]

    near_duplicate_groups = (
        detector.find_near_duplicates(
            file_paths
        )
    )

    print()
    print("=" * 60)
    print("DETECTION RESULT")
    print("=" * 60)

    print(
        f"Near-duplicate groups: "
        f"{detector.get_near_duplicate_group_count(
            near_duplicate_groups
        )}"
    )

    print(
        f"Near-duplicate files: "
        f"{detector.get_near_duplicate_file_count(
            near_duplicate_groups
        )}"
    )

    print(
        f"Recoverable storage: "
        f"{detector.get_near_duplicate_storage_bytes(
            near_duplicate_groups
        )} bytes"
    )

    if near_duplicate_groups:

        for group_number, (
            representative_hash,
            paths,
        ) in enumerate(
            near_duplicate_groups.items(),
            start=1,
        ):

            print()
            print(
                f"Group #{group_number}"
            )

            print(
                f"Representative hash: "
                f"{representative_hash}"
            )

            for path in paths:

                print(
                    f"  - {path.name}"
                )

    else:

        print(
            "No near-duplicate groups detected."
        )

    # --------------------------------------------------
    # CLEANUP
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("CLEANUP")
    print("=" * 60)

    if TEST_IMAGE.exists():

        TEST_IMAGE.unlink()

        print(
            "Temporary test image removed."
        )

    print()
    print("Test completed.")


if __name__ == "__main__":
    main()