from app.scanner.file_scanner import FileScanner
from app.scanner.metadata import MetadataExtractor


def main():
    scanner = FileScanner()
    metadata_extractor = MetadataExtractor()

    directory_path = input(
        "Enter the folder path you want to scan: "
    ).strip()

    try:
        files = scanner.scan_directory(directory_path)

        print("\nScan completed successfully.")
        print(f"Supported files found: {len(files)}\n")

        for file_path in files:
            metadata = metadata_extractor.extract(file_path)

            print("-" * 60)
            print(f"Name: {metadata.file_name}")
            print(f"Path: {metadata.file_path}")
            print(f"Extension: {metadata.extension}")
            print(f"Size: {metadata.size_bytes} bytes")
            print(f"Created: {metadata.created_at}")
            print(f"Modified: {metadata.modified_at}")
            print(f"Accessed: {metadata.accessed_at}")
            print(f"MIME Type: {metadata.mime_type}")

    except (
        FileNotFoundError,
        NotADirectoryError,
        ValueError,
    ) as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()