
import streamlit as st

from app.database.database import Database
from app.duplicates.duplicate_analytics_service import DuplicateAnalyticsService
from app.duplicates.near_duplicate_analytics_service import (
    NearDuplicateAnalyticsService,
)
from app.services.scan_service import ScanService
from app.services.storage_analytics_service import StorageAnalyticsService


# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Digital Junk AI",
    page_icon="🧹",
    layout="wide",
)


# ---------------------------------------------------------
# Services
# ---------------------------------------------------------

database = Database()

storage_analytics_service = StorageAnalyticsService(
    database=database
)

duplicate_analytics_service = DuplicateAnalyticsService(
    database=database
)

near_duplicate_analytics_service = NearDuplicateAnalyticsService(
    database=database
)

scan_service = ScanService(
    database=database
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("🧹 Digital Junk AI")
st.caption("Your AI-powered digital decluttering assistant.")

st.divider()


# ---------------------------------------------------------
# Scan Section
# ---------------------------------------------------------

st.header("📂 Scan Directory")

directory = st.text_input(
    "Enter directory path",
    placeholder=r"C:\Users\YourName\Downloads",
)


if st.button("🔍 Start Scan", type="primary"):

    if not directory.strip():
        st.error("Please enter a directory path.")

    else:

        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(current, total, file_path):

            if total > 0:
                progress = current / total
                progress_bar.progress(progress)

            status_text.text(
                f"Scanning {current}/{total}: {file_path}"
            )

        try:

            with st.spinner("Scanning files..."):

                result = scan_service.scan(
                    directory,
                    progress_callback=update_progress,
                )

            progress_bar.progress(1.0)

            status_text.success("Scan completed successfully.")

            st.success(
                f"Scan completed. "
                f"{result.successful_count} files processed."
            )

            if result.failed_count > 0:

                st.warning(
                    f"{result.failed_count} files could not be processed."
                )

        except Exception as error:

            st.error(
                f"Scan failed: {error}"
            )


st.divider()


# ---------------------------------------------------------
# Storage Overview
# ---------------------------------------------------------

st.header("💾 Storage Overview")

try:

    storage_summary = (
        storage_analytics_service
        .get_storage_summary()
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Files",
            storage_summary.get("total_files", 0),
        )

    with col2:

        total_size_bytes = storage_summary.get(
            "total_size_bytes",
            0,
        )

        total_size_mb = (
            total_size_bytes / (1024 * 1024)
        )

        st.metric(
            "Total Storage",
            f"{total_size_mb:.2f} MB",
        )

    with col3:

        st.metric(
            "File Types",
            storage_summary.get(
                "total_extensions",
                0,
            ),
        )

except Exception as error:

    st.warning(
        f"Storage analytics unavailable: {error}"
    )


st.divider()


# ---------------------------------------------------------
# Storage By Extension
# ---------------------------------------------------------

st.header("📊 Storage by Extension")

try:

    storage_by_extension = (
        storage_analytics_service
        .get_storage_by_extension()
    )

    if storage_by_extension:

        extension_data = []

        for row in storage_by_extension:

            extension_data.append(
                {
                    "Extension": row.get(
                        "extension",
                        "",
                    ),
                    "Files": row.get(
                        "file_count",
                        0,
                    ),
                    "Storage (MB)": round(
                        row.get(
                            "total_size_bytes",
                            0,
                        )
                        / (1024 * 1024),
                        2,
                    ),
                }
            )

        st.dataframe(
            extension_data,
            use_container_width=True,
        )

    else:

        st.info(
            "No storage data available yet."
        )

except Exception as error:

    st.warning(
        f"Unable to load extension analytics: {error}"
    )


st.divider()


# ---------------------------------------------------------
# Storage By Category
# ---------------------------------------------------------

st.header("📁 Storage by Category")

try:

    storage_by_category = (
        storage_analytics_service
        .get_storage_by_category()
    )

    if storage_by_category:

        category_data = []

        for row in storage_by_category:

            category_data.append(
                {
                    "Category": row.get(
                        "category",
                        "Unknown",
                    ),
                    "Files": row.get(
                        "file_count",
                        0,
                    ),
                    "Storage (MB)": round(
                        row.get(
                            "total_size_bytes",
                            0,
                        )
                        / (1024 * 1024),
                        2,
                    ),
                }
            )

        st.dataframe(
            category_data,
            use_container_width=True,
        )

    else:

        st.info(
            "No category data available yet."
        )

except Exception as error:

    st.warning(
        f"Unable to load category analytics: {error}"
    )


st.divider()


# ---------------------------------------------------------
# Largest Files
# ---------------------------------------------------------

st.header("📦 Largest Files")

try:

    largest_files = (
        storage_analytics_service
        .get_largest_files(limit=10)
    )

    if largest_files:

        largest_file_data = []

        for file in largest_files:

            largest_file_data.append(
                {
                    "File": file.get(
                        "file_path",
                        "",
                    ),
                    "Size (MB)": round(
                        file.get(
                            "size_bytes",
                            0,
                        )
                        / (1024 * 1024),
                        2,
                    ),
                }
            )

        st.dataframe(
            largest_file_data,
            use_container_width=True,
        )

    else:

        st.info(
            "No files available."
        )

except Exception as error:

    st.warning(
        f"Unable to load largest files: {error}"
    )


st.divider()


# ---------------------------------------------------------
# Exact Duplicate Insights
# ---------------------------------------------------------

st.header("♻️ Duplicate Insights")

try:

    duplicate_summary = (
        duplicate_analytics_service
        .get_duplicate_summary()
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Duplicate Groups",
            duplicate_summary.get(
                "duplicate_group_count",
                0,
            ),
        )

    with col2:

        st.metric(
            "Duplicate Files",
            duplicate_summary.get(
                "duplicate_file_count",
                0,
            ),
        )

    with col3:

        duplicate_storage_bytes = (
            duplicate_summary.get(
                "duplicate_storage_bytes",
                0,
            )
        )

        duplicate_storage_mb = (
            duplicate_storage_bytes
            / (1024 * 1024)
        )

        st.metric(
            "Recoverable Storage",
            f"{duplicate_storage_mb:.2f} MB",
        )


    largest_duplicate_groups = (
        duplicate_analytics_service
        .get_largest_duplicate_groups(
            limit=5
        )
    )

    if largest_duplicate_groups:

        st.subheader(
            "Largest Duplicate Groups"
        )

        duplicate_group_data = []

        for group in largest_duplicate_groups:

            duplicate_group_data.append(
                {
                    "Group ID": group.get(
                        "id",
                        "",
                    ),
                    "Files": group.get(
                        "file_count",
                        0,
                    ),
                    "Total Size (MB)": round(
                        group.get(
                            "total_size_bytes",
                            0,
                        )
                        / (1024 * 1024),
                        2,
                    ),
                    "Recoverable (MB)": round(
                        group.get(
                            "duplicate_size_bytes",
                            0,
                        )
                        / (1024 * 1024),
                        2,
                    ),
                }
            )

        st.dataframe(
            duplicate_group_data,
            use_container_width=True,
        )

    else:

        st.info(
            "No exact duplicate groups found."
        )

except Exception as error:

    st.warning(
        f"Duplicate analytics unavailable: {error}"
    )


st.divider()


# ---------------------------------------------------------
# Near-Duplicate Insights
# ---------------------------------------------------------

st.header("🖼️ Near-Duplicate Insights")

try:

    near_duplicate_summary = (
        near_duplicate_analytics_service
        .get_near_duplicate_summary()
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Near-Duplicate Groups",
            near_duplicate_summary.get(
                "near_duplicate_group_count",
                0,
            ),
        )

    with col2:

        st.metric(
            "Near-Duplicate Files",
            near_duplicate_summary.get(
                "near_duplicate_file_count",
                0,
            ),
        )

    with col3:

        near_duplicate_storage_bytes = (
            near_duplicate_summary.get(
                "duplicate_storage_bytes",
                0,
            )
        )

        near_duplicate_storage_mb = (
            near_duplicate_storage_bytes
            / (1024 * 1024)
        )

        st.metric(
            "Recoverable Storage",
            f"{near_duplicate_storage_mb:.2f} MB",
        )


    largest_near_duplicates = (
        near_duplicate_analytics_service
        .get_largest_near_duplicate_groups(
            limit=5
        )
    )

    if largest_near_duplicates:

        st.subheader(
            "Largest Near-Duplicate Groups"
        )

        near_duplicate_group_data = []

        for group in largest_near_duplicates:

            near_duplicate_group_data.append(
                {
                    "Group ID": group.get(
                        "id",
                        "",
                    ),
                    "Files": group.get(
                        "file_count",
                        0,
                    ),
                    "Total Size (MB)": round(
                        group.get(
                            "total_size_bytes",
                            0,
                        )
                        / (1024 * 1024),
                        2,
                    ),
                    "Recoverable (MB)": round(
                        group.get(
                            "duplicate_size_bytes",
                            0,
                        )
                        / (1024 * 1024),
                        2,
                    ),
                    "Threshold": group.get(
                        "similarity_threshold",
                        8,
                    ),
                }
            )

        st.dataframe(
            near_duplicate_group_data,
            use_container_width=True,
        )

    else:

        st.info(
            "No near-duplicate image groups found."
        )

except Exception as error:

    st.warning(
        f"Near-duplicate analytics unavailable: {error}"
    )


st.divider()


# ---------------------------------------------------------
# Scan History
# ---------------------------------------------------------

st.header("🕘 Scan History")

try:

    scan_history = (
        storage_analytics_service
        .get_scan_history()
    )

    if scan_history:

        scan_history_data = []

        for scan in scan_history:

            scan_history_data.append(
                {
                    "Scan ID": scan.get(
                        "id",
                        "",
                    ),
                    "Directory": scan.get(
                        "directory_path",
                        "",
                    ),
                    "Files Found": scan.get(
                        "files_found",
                        0,
                    ),
                    "Processed": scan.get(
                        "files_processed",
                        0,
                    ),
                    "Failed": scan.get(
                        "files_failed",
                        0,
                    ),
                    "Size (MB)": round(
                        scan.get(
                            "total_size_bytes",
                            0,
                        )
                        / (1024 * 1024),
                        2,
                    ),
                    "Status": scan.get(
                        "status",
                        "",
                    ),
                    "Created": scan.get(
                        "created_at",
                        "",
                    ),
                }
            )

        st.dataframe(
            scan_history_data,
            use_container_width=True,
        )

    else:

        st.info(
            "No scan history available."
        )

except Exception as error:

    st.warning(
        f"Unable to load scan history: {error}"
    )


st.divider()


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.caption(
    "Digital Junk AI — Your AI-powered digital decluttering assistant."
)
