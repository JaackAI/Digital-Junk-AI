import streamlit as st

from app.services.scan_service import ScanService
from app.services.storage_analytics_service import (
    StorageAnalyticsService,
)
from app.utils.formatting import format_bytes


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Digital Junk AI",
    page_icon="🧹",
    layout="wide",
)


# ==================================================
# SERVICES
# ==================================================

scan_service = ScanService()
analytics_service = StorageAnalyticsService()


# ==================================================
# HEADER
# ==================================================

st.title("🧹 Digital Junk AI")

st.caption(
    "Your AI-powered digital decluttering assistant"
)

st.divider()


# ==================================================
# LOAD ANALYTICS
# ==================================================

latest_scan = analytics_service.get_latest_scan()

scan_history = analytics_service.get_scan_history()


if latest_scan:

    summary = (
        analytics_service.get_latest_scan_storage_summary()
    )

    categories = (
        analytics_service.get_latest_scan_storage_by_category()
    )

    largest_files = (
        analytics_service.get_latest_scan_largest_files(
            limit=10
        )
    )

else:

    summary = {
        "total_files": 0,
        "total_size_bytes": 0,
    }

    categories = []

    largest_files = []


# ==================================================
# CALCULATE DASHBOARD METRICS
# ==================================================

total_files = summary["total_files"]

total_size_bytes = summary["total_size_bytes"]

total_categories = len(categories)

largest_file_size = (
    largest_files[0]["size_bytes"]
    if largest_files
    else 0
)


# ==================================================
# LATEST SCAN OVERVIEW
# ==================================================

st.subheader("📊 Latest Scan Overview")

if latest_scan:

    st.caption(
        f"Showing analytics for scan #{latest_scan['id']}: "
        f"{latest_scan['directory_path']}"
    )

else:

    st.caption(
        "No scans have been completed yet."
    )


# ==================================================
# KPI CARDS
# ==================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        label="Total Files",
        value=f"{total_files:,}",
    )

with col2:

    st.metric(
        label="Storage Used",
        value=format_bytes(
            total_size_bytes
        ),
    )

with col3:

    st.metric(
        label="File Categories",
        value=total_categories,
    )

with col4:

    st.metric(
        label="Largest File",
        value=format_bytes(
            largest_file_size
        ),
    )


st.divider()


# ==================================================
# STORAGE BY CATEGORY
# ==================================================

st.subheader("📁 Storage by Category")

if categories:

    category_names = [
        item["category"]
        for item in categories
    ]

    category_sizes = [
        item["total_size_bytes"]
        for item in categories
    ]

    chart_data = {
        "Category": category_names,
        "Storage": category_sizes,
    }

    st.bar_chart(
        chart_data,
        x="Category",
        y="Storage",
    )

else:

    st.info(
        "No category data available yet."
    )


st.divider()


# ==================================================
# CATEGORY DETAILS
# ==================================================

st.subheader("📋 Category Details")

if categories:

    for category in categories:

        col1, col2, col3 = st.columns(3)

        with col1:

            st.write(
                f"**{category['category']}**"
            )

        with col2:

            st.write(
                f"{category['file_count']:,} files"
            )

        with col3:

            st.write(
                format_bytes(
                    category["total_size_bytes"]
                )
            )

else:

    st.info(
        "No category information available."
    )


st.divider()


# ==================================================
# LARGEST FILES
# ==================================================

st.subheader("📦 Largest Files in Latest Scan")

if largest_files:

    for file in largest_files:

        col1, col2, col3 = st.columns(
            [5, 1, 2]
        )

        with col1:

            st.write(
                f"**{file['file_name']}**"
            )

        with col2:

            st.write(
                file["extension"]
            )

        with col3:

            st.write(
                format_bytes(
                    file["size_bytes"]
                )
            )

else:

    st.info(
        "No files available yet."
    )


# ==================================================
# SCAN HISTORY
# ==================================================

st.divider()

st.subheader("🕘 Scan History")

if scan_history:

    for scan in scan_history:

        scan_id = scan["id"]

        directory_path = scan["directory_path"]

        started_at = scan["started_at"]

        completed_at = scan["completed_at"]

        files_found = scan["files_found"]

        files_processed = scan["files_processed"]

        files_failed = scan["files_failed"]

        total_size_bytes = scan["total_size_bytes"]

        with st.expander(
            f"Scan #{scan_id} — {directory_path}"
        ):

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**Started:** {started_at}"
                )

                st.write(
                    f"**Completed:** {completed_at}"
                )

                st.write(
                    f"**Files Found:** {files_found}"
                )

                st.write(
                    f"**Files Processed:** "
                    f"{files_processed}"
                )

            with col2:

                st.write(
                    f"**Files Failed:** "
                    f"{files_failed}"
                )

                st.write(
                    f"**Total Size:** "
                    f"{format_bytes(total_size_bytes)}"
                )

            st.write("### Files in This Scan")

            scan_files = (
                analytics_service.get_files_by_scan(
                    scan_id
                )
            )

            if scan_files:

                for scanned_file in scan_files:

                    file_col1, file_col2, file_col3 = (
                        st.columns([5, 1, 2])
                    )

                    with file_col1:

                        st.write(
                            f"**{scanned_file['file_name']}**"
                        )

                    with file_col2:

                        st.write(
                            scanned_file["extension"]
                        )

                    with file_col3:

                        st.write(
                            format_bytes(
                                scanned_file["size_bytes"]
                            )
                        )

            else:

                st.info(
                    "No files found for this scan."
                )

else:

    st.info(
        "No scan history available yet."
    )


# ==================================================
# SCAN SECTION
# ==================================================

st.divider()

st.subheader("🔍 Scan a Folder")

directory = st.text_input(
    "Folder path",
    placeholder=(
        r"C:\Users\AMD\Desktop\Tested"
    ),
)


if st.button(
    "🚀 Start Scan",
    type="primary",
):

    if not directory.strip():

        st.warning(
            "Please enter a folder path."
        )

    else:

        try:

            with st.spinner(
                "Scanning files..."
            ):

                progress_bar = st.progress(0)

                progress_text = st.empty()

                def update_progress(
                    current_file,
                    total_files,
                    current_file_path,
                ):
                    if total_files > 0:

                        progress_value = (
                            current_file / total_files
                        )

                        progress_bar.progress(
                            progress_value
                        )

                        progress_text.write(
                            f"Processing file "
                            f"{current_file} "
                            f"of {total_files}: "
                            f"{current_file_path.name}"
                        )

                    else:

                        progress_bar.progress(1.0)

                        progress_text.write(
                            "No supported files found."
                        )

                result = scan_service.scan(
                    directory,
                    progress_callback=update_progress,
                )

                progress_text.success(
                    "File processing completed."
                )

            st.success(
                "Scan completed successfully."
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Files Found",
                    (
                        result.successful_count
                        + result.failed_count
                    ),
                )

            with col2:

                st.metric(
                    "Processed",
                    result.successful_count,
                )

            with col3:

                st.metric(
                    "Failed",
                    result.failed_count,
                )

            if result.errors:

                st.warning(
                    "Some files could not be processed."
                )

                st.write("### Failed Files")

                for scan_error in result.errors:

                    st.write(
                        f"**File:** "
                        f"{scan_error.file_path}"
                    )

                    st.write(
                        f"**Reason:** "
                        f"{scan_error.error_message}"
                    )

                    st.divider()

            st.rerun()

        except (
            FileNotFoundError,
            NotADirectoryError,
        ) as error:

            st.error(
                str(error)
            )

        except Exception as error:

            st.error(
                f"Unexpected error: {error}"
            )