from app.services.storage_analytics_service import (
    StorageAnalyticsService,
)


def main():

    service = StorageAnalyticsService()

    # ==================================================
    # SCAN HISTORY
    # ==================================================

    print("\nSCAN HISTORY")
    print("=" * 80)

    scans = service.get_scan_history()

    for scan in scans:

        print(
            f"Scan #{scan['id']} | "
            f"{scan['directory_path']} | "
            f"Files: {scan['files_processed']} | "
            f"Failed: {scan['files_failed']} | "
            f"Size: {scan['total_size_bytes']} bytes"
        )

    # ==================================================
    # LATEST SCAN
    # ==================================================

    print("\nLATEST SCAN")
    print("=" * 80)

    latest_scan = service.get_latest_scan()

    if latest_scan:

        print(
            f"Scan ID: {latest_scan['id']}"
        )

        print(
            f"Directory: "
            f"{latest_scan['directory_path']}"
        )

        print(
            f"Files processed: "
            f"{latest_scan['files_processed']}"
        )

        print(
            f"Files failed: "
            f"{latest_scan['files_failed']}"
        )

    else:

        print("No scans found.")

    # ==================================================
    # FILES FROM LATEST SCAN
    # ==================================================

    if latest_scan:

        print("\nFILES FROM LATEST SCAN")
        print("=" * 80)

        files = service.get_files_by_scan(
            latest_scan["id"]
        )

        for file in files:

            print(
                f"{file['file_name']} | "
                f"{file['extension']} | "
                f"{file['size_bytes']} bytes"
            )


if __name__ == "__main__":
    main()