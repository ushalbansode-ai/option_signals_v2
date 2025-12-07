import json
import os
from datetime import datetime
from typing import List


HISTORY_FILE = "src/output/chain_history.json"
MAX_HISTORY = 40 # keep last 40 snapshots




def _ensure_dir(path):
d = os.path.dirname(path)
if d and not os.path.exists(d):
os.makedirs(d, exist_ok=True)




def load_history() -> List[dict]:
_ensure_dir(HISTORY_FILE)
if not os.path.exists(HISTORY_FILE):
return []
try:
with open(HISTORY_FILE, "r") as f:
data = json.load(f)
return data if isinstance(data, list) else []
except Exception:
return []




def save_snapshot(snapshot: dict) -> List[dict]:
"""Save a new snapshot to history and return the trimmed history list.


snapshot should be a dict with at least:
- timestamp (ISO string)
- symbol
- data: raw parsed chain (list of rows)
"""
_ensure_dir(HISTORY_FILE)
history = load_history()


history.append(snapshot)
history = history[-MAX_HISTORY:]


with open(HISTORY_FILE, "w") as f:
json.dump(history, f, indent=2)


return history




def last_n(n: int = 10) -> List[dict]:
h = load_history()
return h[-n:]
