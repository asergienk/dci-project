from datetime import datetime


def sort_by_created_at(items):
    return sorted(
        items, key=lambda x: datetime.strptime(x["created_at"], "%Y-%m-%dT%H:%M:%S.%f"),
    )