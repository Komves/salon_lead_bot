CATALOG = {
    "Стрижка": ["Анна Иванова", "Ольга Петрова"],
    "Окрашивание": ["Анна Иванова"],
    "Маникюр": ["Мария Соколова"],
}

SERVICES = list(CATALOG.keys())


def get_specialists(service: str) -> list[str]:
    return CATALOG.get(service, [])
