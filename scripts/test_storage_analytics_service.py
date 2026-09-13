from app.services.storage_analytics_service import (
    StorageAnalyticsService,
)


def main():

    service = StorageAnalyticsService()

    # ==================================================
    # STORAGE SUMMARY
    # ==================================================

    print("\nSTORAGE SUMMARY")
    print("=" * 60)

    summary = service.get_storage_summary()

    print(f"Total files: {summary['total_files']}")
    print(
        f"Total size: {summary['total_size_bytes']} bytes"
    )

    # ==================================================
    # STORAGE BY CATEGORY
    # ==================================================

    print("\nSTORAGE BY CATEGORY")
    print("=" * 60)

    categories = service.get_storage_by_category()

    for category in categories:
        print(
            f"{category['category']:12} | "
            f"Files: {category['file_count']:3} | "
            f"Size: "
            f"{category['total_size_bytes']} bytes"
        )

    # ==================================================
    # LARGEST FILES
    # ==================================================

    print("\nLARGEST FILES")
    print("=" * 60)

    largest_files = service.get_largest_files(limit=5)

    for file in largest_files:
        print(
            f"{file['file_name']:45} | "
            f"{file['size_bytes']} bytes"
        )


if __name__ == "__main__":
    main()