import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "counts.json")

FLAVORS = ["concord_grape", "strawberry", "white_grape_raspberry", "orange", "white_grape_peach"]

FLAVOR_LABELS = {
    "concord_grape": "Concord Grape",
    "strawberry": "Strawberry",
    "white_grape_raspberry": "White Grape Raspberry",
    "orange": "Orange",
    "white_grape_peach": "White Grape Peach",
}


def _empty_scaffold() -> dict:
    return {
        "sessions": [],
        "totals": {f: 0 for f in FLAVORS},
        "grand_total": 0,
    }


def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return _empty_scaffold()
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def _write_data(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save_session(counts: dict, image_filename: str, notes: str = "") -> None:
    data = load_data()

    # Normalize — ensure all flavors present, coerce to int
    normalized = {f: int(counts.get(f, 0)) for f in FLAVORS}
    session_total = sum(normalized.values())

    session = {
        "id": datetime.now().isoformat(timespec="seconds"),
        "image_filename": image_filename,
        "counts": normalized,
        "total": session_total,
        "notes": notes,
    }
    data["sessions"].append(session)

    # Recompute running totals
    for flavor in FLAVORS:
        data["totals"][flavor] = data["totals"].get(flavor, 0) + normalized[flavor]
    data["grand_total"] = data.get("grand_total", 0) + session_total

    _write_data(data)


def delete_session(session_id: str) -> bool:
    data = load_data()
    original_len = len(data["sessions"])
    data["sessions"] = [s for s in data["sessions"] if s["id"] != session_id]

    if len(data["sessions"]) == original_len:
        return False

    # Recompute totals from scratch
    totals = {f: 0 for f in FLAVORS}
    grand_total = 0
    for session in data["sessions"]:
        for flavor in FLAVORS:
            totals[flavor] += session["counts"].get(flavor, 0)
        grand_total += session["total"]

    data["totals"] = totals
    data["grand_total"] = grand_total
    _write_data(data)
    return True


def get_totals() -> dict:
    return load_data()["totals"]


def get_sessions() -> list:
    return load_data()["sessions"]


def get_grand_total() -> int:
    return load_data()["grand_total"]
