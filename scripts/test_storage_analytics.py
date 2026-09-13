from app.database.database import Database


def main():
    database = Database()

    database.initialize()
    database.migrate_scan_statistics()

    # ==================================================
    # STORAGE SUMMARY
    # ==================================================

    print("\nSTORAGE SUMMARY")
    print("=" * 60)

    summary = database.get_storage_summary()

    print(f"Total files: {summary['total_files']}")
    print(
        f"Total size: {summary['total_size_bytes']} bytes"
    )

    # ==================================================
    # STORAGE BY EXTENSION
    # ==================================================

    print("\nSTORAGE BY EXTENSION")
    print("=" * 60)

    storage_by_extension = (
        database.get_storage_by_extension()
    )

    for item in storage_by_extension:
        print(
            f"{item['extension']:8} | "
            f"Files: {item['file_count']:3} | "
            f"Size: {item['total_size_bytes']} bytes"
        )

    # ==================================================
    # STORAGE BY CATEGORY
    # ==================================================

    print("\nSTORAGE BY CATEGORY")
    print("=" * 60)

    storage_by_category = (
        database.get_storage_by_category()
    )

    for item in storage_by_category:
        print(
            f"{item['category']:12} | "
            f"Files: {item['file_count']:3} | "
            f"Size: {item['total_size_bytes']} bytes"
        )

    # ==================================================
    # LARGEST FILES
    # ==================================================

    print("\nLARGEST FILES")
    print("=" * 60)

    largest_files = database.get_largest_files(limit=5)

    for file in largest_files:
        print(
            f"{file['file_name']:45} | "
            f"{file['size_bytes']} bytes"
        )


if __name__ == "__main__":
    main()