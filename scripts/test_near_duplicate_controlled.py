import sys
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)

from app.duplicates.perceptual_hash_detector import (
    PerceptualHashDetector,
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

    detector = PerceptualHashDetector()

    print("=" * 60)
    print("CONTROLLED NEAR-DUPLICATE TEST")
    print("=" * 60)

    if not ORIGINAL_IMAGE.exists():

        print(
            f"Original image not found: "
            f"{ORIGINAL_IMAGE}"
        )

        return

    print(
        f"Original: {ORIGINAL_IMAGE.name}"
    )

    # Create a modified copy.
    with Image.open(ORIGINAL_IMAGE) as image:

        image = image.convert("RGB")

        original_width, original_height = image.size

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
        f"Test image created: "
        f"{TEST_IMAGE.name}"
    )

    print(
        f"Original size: "
        f"{original_width} x {original_height}"
    )

    print(
        f"Modified size: "
        f"{new_width} x {new_height}"
    )

    print()
    print("=" * 60)
    print("HASH COMPARISON")
    print("=" * 60)

    original_hash = detector.calculate_phash(
        ORIGINAL_IMAGE
    )

    test_hash = detector.calculate_phash(
        TEST_IMAGE
    )

    distance = detector.calculate_distance(
        original_hash,
        test_hash,
    )

    similar = detector.are_similar(
        original_hash,
        test_hash,
    )

    print(
        f"Original pHash: {original_hash}"
    )

    print(
        f"Modified pHash: {test_hash}"
    )

    print(
        f"Distance: {distance}"
    )

    print(
        f"Similar with threshold 8: {similar}"
    )

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