from app.duplicates.hash_detector import FileHashDetector


detector = FileHashDetector()

file_path = r"C:\Users\AMD\Desktop\Tested"

print(
    "Testing hash detector..."
)

from pathlib import Path

files = [
    path
    for path in Path(file_path).rglob("*")
    if path.is_file()
]

for file in files[:5]:

    try:

        file_hash = detector.calculate_sha256(
            file
        )

        print(
            f"{file.name}"
        )

        print(
            f"SHA-256: {file_hash}"
        )

        print("-" * 60)

    except Exception as error:

        print(
            f"Failed: {file}"
        )

        print(
            f"Reason: {error}"
        )

print(
    "Hash testing completed."
)