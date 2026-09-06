from app.database.database import Database


def main():
    database = Database()

    database.initialize()
    database.migrate_scan_statistics()

    # ==================================================
    # TEST 1: SCAN HISTORY
    # ==================================================

    print("\nSCAN HISTORY")
    print("=" * 80)

    scans = database.get_scan_history()

    for scan in scans:
        print(scan)

    # ==================================================
    # TEST 2: LATEST SCAN
    # ==================================================

    print("\nLATEST SCAN")
    print("=" * 80)

    latest_scan = database.get_latest_scan()

    print(latest_scan)

    # ==================================================
    # TEST 3: GET SCAN BY ID
    # ==================================================

    if latest_scan is not None:

        scan_id = latest_scan["id"]

        print("\nSCAN BY ID")
        print("=" * 80)

        scan = database.get_scan_by_id(scan_id)

        print(scan)

        # ==============================================
        # TEST 4: FILES IN SCAN
        # ==============================================

        print("\nFILES IN LATEST SCAN")
        print("=" * 80)

        files = database.get_files_by_scan(scan_id)

        for file in files:
            print(file)


if __name__ == "__main__":
    main()