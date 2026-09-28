import sys
from pathlib import Path


# Add the project root to Python's import path.
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


def main():
    detector = PerceptualHashDetector()

    image_files = [
        file_path
        for file_path in TEST_DIRECTORY.rglob("*")
        if file_path.is_file()
        and file_path.suffix.lower()
        in detector.SUPPORTED_EXTENSIONS
    ]

    print("=" * 60)
    print("PERCEPTUAL HASH TEST")
    print("=" * 60)

    print(f"Test directory: {TEST_DIRECTORY}")
    print(f"Images found: {len(image_files)}")
    print()

    if not image_files:
        print("No supported images found.")
        return

    hashes = {}

    for image_path in image_files:

        try:

            image_hash = detector.calculate_phash(
                image_path
            )

            hashes[image_path] = image_hash

            print(
                f"{image_path.name}"
            )

            print(
                f"  pHash: {image_hash}"
            )

        except Exception as error:

            print(
                f"ERROR: {image_path}"
            )

            print(
                f"  {error}"
            )

    print()
    print("=" * 60)
    print("PAIRWISE SIMILARITY")
    print("=" * 60)

    paths = list(hashes.keys())

    if len(paths) < 2:

        print(
            "At least two images are required "
            "for similarity testing."
        )

        return

    for index in range(len(paths)):

        for second_index in range(
            index + 1,
            len(paths),
        ):

            first_path = paths[index]
            second_path = paths[second_index]

            distance = detector.calculate_distance(
                hashes[first_path],
                hashes[second_path],
            )

            similar = detector.are_similar(
                hashes[first_path],
                hashes[second_path],
            )

            print()
            print(
                f"{first_path.name}"
            )

            print(
                f"vs {second_path.name}"
            )

            print(
                f"  Distance: {distance}"
            )

            print(
                f"  Similar: {similar}"
            )


if __name__ == "__main__":
    main()