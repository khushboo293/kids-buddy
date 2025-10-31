import os, json, datetime
from typing import List, Dict, Any

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "sessions")
os.makedirs(LOG_DIR, exist_ok=True)

def _session_path(session_id: str) -> str:
    return os.path.join(LOG_DIR, f"{session_id}.json")

def start_session() -> str:
    sid = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    data = {"id": sid, "started": datetime.datetime.now().isoformat(), "turns": [], "stars": 0}
    with open(_session_path(sid), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return sid

def append_turn(session_id: str, role: str, text: str):
    path = _session_path(session_id)
    data = json.load(open(path, "r", encoding="utf-8"))
    data["turns"].append({"ts": datetime.datetime.now().isoformat(), "role": role, "text": text, "len": len(text.split())})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def set_stars(session_id: str, stars: int):
    path = _session_path(session_id)
    data = json.load(open(path, "r", encoding="utf-8"))
    data["stars"] = stars
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def list_sessions() -> List[Dict[str, Any]]:
    items = []
    for name in sorted(os.listdir(LOG_DIR)):
        if name.endswith(".json"):
            p = os.path.join(LOG_DIR, name)
            try:
                items.append(json.load(open(p, "r", encoding="utf-8")))
            except Exception:
                pass
    return items
