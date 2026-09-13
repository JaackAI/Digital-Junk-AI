def format_bytes(size_bytes: int) -> str:
    """
    Convert bytes into a human-readable file size.
    """

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"

    if size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"

    if size_bytes < 1024 ** 4:
        return f"{size_bytes / (1024 ** 3):.2f} GB"

    return f"{size_bytes / (1024 ** 4):.2f} TB"