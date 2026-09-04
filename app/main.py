from app.services.scan_service import ScanService


def main():
    scan_service = ScanService()

    directory_path = input(
        "Enter the folder path you want to scan: "
    ).strip()

    try:
        result = scan_service.scan(directory_path)

        print("\nScan completed successfully.")
        print(
            f"Supported files found: "
            f"{result.successful_count}"
        )

        for metadata in result.files:
            print("-" * 60)
            print(f"Name: {metadata.file_name}")
            print(f"Path: {metadata.file_path}")
            print(f"Extension: {metadata.extension}")
            print(f"Size: {metadata.size_bytes} bytes")
            print(f"Created: {metadata.created_at}")
            print(f"Modified: {metadata.modified_at}")
            print(f"Accessed: {metadata.accessed_at}")
            print(f"MIME Type: {metadata.mime_type}")

        print("\nScan Summary")
        print(
            f"Successfully processed: "
            f"{result.successful_count}"
        )
        print(
            f"Failed to process: "
            f"{result.failed_count}"
        )

        if result.errors:
            print("\nErrors:")

            for scan_error in result.errors:
                print(
                    f"- {scan_error.file_path}: "
                    f"{scan_error.error_message}"
                )

    except (
        FileNotFoundError,
        NotADirectoryError,
        ValueError,
    ) as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()