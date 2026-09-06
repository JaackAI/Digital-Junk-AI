from app.database.database import Database


def main():
    database = Database()
    database.initialize()
    database.migrate_scan_statistics()

    with database.get_connection() as connection:
        cursor = connection.cursor()

        print("\nSCANS")
        print("-" * 80)

        cursor.execute(
            """
            SELECT
                id,
                directory_path,
                started_at,
                completed_at,
                files_found,
                files_processed,
                files_failed,
                total_size_bytes
            FROM scans
            ORDER BY id
            """
        )

        for row in cursor.fetchall():
            print(row)

        print("\nFILES")
        print("-" * 80)

        cursor.execute(
            """
            SELECT
                id,
                scan_id,
                file_name,
                extension,
                size_bytes,
                mime_type
            FROM files
            ORDER BY id
            """
        )

        for row in cursor.fetchall():
            print(row)


if __name__ == "__main__":
    main()