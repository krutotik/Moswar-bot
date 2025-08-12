from datetime import datetime


def parse_date(date_str: str) -> datetime:
    """
    Extracts a Russian date-time string like:
    '18 августа 2025 20:13'
    and returns a datetime object.
    """
    month_map: dict[str, int] = {
        "января": 1,
        "февраля": 2,
        "марта": 3,
        "апреля": 4,
        "мая": 5,
        "июня": 6,
        "июля": 7,
        "августа": 8,
        "сентября": 9,
        "октября": 10,
        "ноября": 11,
        "декабря": 12,
    }

    date_str = date_str.lower()
    for name, num in month_map.items():
        if name in date_str:
            date_str = date_str.replace(name, str(num))
            break

    return datetime.strptime(date_str, "%d %m %Y %H:%M")
