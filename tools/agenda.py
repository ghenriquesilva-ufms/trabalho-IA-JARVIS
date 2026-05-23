import json
import os
import unicodedata
from datetime import date, datetime, timedelta
from typing import Any, Dict, List


_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "agenda.json")


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii").lower()


def _load_events() -> List[Dict[str, Any]]:
    if not os.path.exists(_DATA_PATH):
        return []
    with open(_DATA_PATH, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []


def _save_events(events: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(_DATA_PATH), exist_ok=True)
    with open(_DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(events, file, ensure_ascii=False, indent=2)


def _parse_event_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _format_event(event: Dict[str, Any]) -> str:
    titulo = event.get("titulo", "(sem titulo)")
    data = event.get("data", "")
    hora = event.get("hora", "")
    tipo = event.get("tipo", "")
    event_id = event.get("id", "")
    return f"#{event_id} | {data} {hora} | {tipo} | {titulo}".strip()


def consultar_agenda(data: str = None) -> str:
    events = _load_events()
    if not events:
        return "Nenhum evento encontrado."

    today = date.today()
    filtered = events

    if data:
        normalized = _normalize_text(data)
        if normalized == "hoje":
            filtered = [event for event in events if _parse_event_date(event["data"]) == today]
        elif normalized == "amanha":
            target = today + timedelta(days=1)
            filtered = [event for event in events if _parse_event_date(event["data"]) == target]
        else:
            weekdays = {
                "segunda": 0,
                "terca": 1,
                "quarta": 2,
                "quinta": 3,
                "sexta": 4,
                "sabado": 5,
                "domingo": 6,
            }
            weekday_index = weekdays.get(normalized)
            if weekday_index is not None:
                week_start = today - timedelta(days=today.weekday())
                target = week_start + timedelta(days=weekday_index)
                filtered = [
                    event for event in events if _parse_event_date(event["data"]) == target
                ]

    if not filtered:
        return "Nenhum evento encontrado."

    filtered.sort(key=lambda event: (event.get("data", ""), event.get("hora", "")))
    return "\n".join(_format_event(event) for event in filtered)
