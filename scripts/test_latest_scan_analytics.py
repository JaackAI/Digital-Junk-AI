from app.services.storage_analytics_service import (
    StorageAnalyticsService,
)


analytics_service = StorageAnalyticsService()

summary = (
    analytics_service.get_latest_scan_storage_summary()
)

categories = (
    analytics_service.get_latest_scan_storage_by_category()
)

print("\nLATEST SCAN STORAGE SUMMARY")
print(summary)

print("\nLATEST SCAN STORAGE BY CATEGORY")

for category in categories:
    print(category)