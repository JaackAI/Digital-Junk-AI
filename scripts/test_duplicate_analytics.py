from app.database.database import Database
from app.duplicates.duplicate_analytics_service import (
    DuplicateAnalyticsService,
)


def main():
    print("=" * 70)
    print("DUPLICATE ANALYTICS TEST")
    print("=" * 70)

    database = Database()

    service = DuplicateAnalyticsService(
        database=database
    )

    # --------------------------------------------------
    # 1. Overall duplicate summary
    # --------------------------------------------------

    print()
    print("DUPLICATE SUMMARY")
    print("-" * 70)

    summary = service.get_duplicate_summary()

    print(
        f"Duplicate groups: "
        f"{summary['duplicate_group_count']}"
    )

    print(
        f"Duplicate files: "
        f"{summary['duplicate_file_count']}"
    )

    print(
        f"Duplicate storage: "
        f"{summary['duplicate_storage_bytes']} bytes"
    )

    assert "duplicate_group_count" in summary
    assert "duplicate_file_count" in summary
    assert "duplicate_storage_bytes" in summary

    assert summary["duplicate_group_count"] >= 1
    assert summary["duplicate_file_count"] >= 2
    assert summary["duplicate_storage_bytes"] > 0

    # --------------------------------------------------
    # 2. Duplicate groups
    # --------------------------------------------------

    print()
    print("DUPLICATE GROUPS")
    print("-" * 70)

    groups = service.get_duplicate_groups()

    print(
        f"Total groups returned: "
        f"{len(groups)}"
    )

    assert len(groups) >= 1

    for group in groups[:5]:

        print(
            f"Group #{group['id']} | "
            f"Scan #{group['scan_id']} | "
            f"Files: {group['file_count']} | "
            f"Total: {group['total_size_bytes']} bytes | "
            f"Duplicate: "
            f"{group['duplicate_size_bytes']} bytes"
        )

    # --------------------------------------------------
    # 3. Test a specific scan
    # --------------------------------------------------

    first_group = groups[0]

    scan_id = first_group["scan_id"]

    print()
    print("SCAN-SPECIFIC SUMMARY")
    print("-" * 70)

    scan_summary = (
        service.get_duplicate_summary_by_scan(
            scan_id
        )
    )

    print(
        f"Scan ID: {scan_id}"
    )

    print(
        f"Duplicate groups: "
        f"{scan_summary['duplicate_group_count']}"
    )

    print(
        f"Duplicate files: "
        f"{scan_summary['duplicate_file_count']}"
    )

    print(
        f"Duplicate storage: "
        f"{scan_summary['duplicate_storage_bytes']} bytes"
    )

    assert scan_summary["duplicate_group_count"] >= 1
    assert scan_summary["duplicate_file_count"] >= 2
    assert scan_summary["duplicate_storage_bytes"] > 0

    # --------------------------------------------------
    # 4. Duplicate group files
    # --------------------------------------------------

    group_id = first_group["id"]

    print()
    print("FILES IN DUPLICATE GROUP")
    print("-" * 70)

    duplicate_files = (
        service.get_duplicate_group_files(
            group_id
        )
    )

    print(
        f"Group ID: {group_id}"
    )

    print(
        f"Files returned: "
        f"{len(duplicate_files)}"
    )

    assert len(duplicate_files) >= 2

    for file in duplicate_files:

        print(
            f"File ID: {file['file_id']} | "
            f"Size: {file['file_size_bytes']} bytes | "
            f"Path: {file['file_path']}"
        )

    # --------------------------------------------------
    # 5. Largest duplicate groups
    # --------------------------------------------------

    print()
    print("LARGEST DUPLICATE GROUPS")
    print("-" * 70)

    largest_groups = (
        service.get_largest_duplicate_groups(
            limit=5
        )
    )

    print(
        f"Groups returned: "
        f"{len(largest_groups)}"
    )

    assert len(largest_groups) >= 1
    assert len(largest_groups) <= 5

    for group in largest_groups:

        print(
            f"Group #{group['id']} | "
            f"Duplicate storage: "
            f"{group['duplicate_size_bytes']} bytes"
        )

    # --------------------------------------------------
    # 6. Test limit validation
    # --------------------------------------------------

    print()
    print("LIMIT VALIDATION")
    print("-" * 70)

    empty_result = (
        service.get_largest_duplicate_groups(
            limit=0
        )
    )

    assert empty_result == []

    print(
        "Limit validation: PASSED"
    )

    # --------------------------------------------------
    # Final result
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("DUPLICATE ANALYTICS TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()