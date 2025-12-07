import json
from datetime import datetime
from .utils_session import get_nse_session
from ..core.history_manager import save_snapshot


API_URL = "https://www.nseindia.com/api/option-chain-indices?symbol={}" # symbol: NIFTY / BANKNIFTY / FINNIFTY




def fetch_option_chain(symbol: str):
session = get_nse_session()
url = API_URL.format(symbol.upper())


try:
r = session.get(url, timeout=10)
r.raise_for_status()
data = r.json()


# Save raw
with open("src/output/latest_raw.json", "w") as f:
json.dump(data, f, indent=2)


# build a lightweight parsed snapshot for history (just the records->data)
parsed_rows = data.get('records', {}).get('data', [])
snapshot = {
'timestamp': data.get('records', {}).get('timestamp') or datetime.utcnow().isoformat(),
'symbol': symbol.upper(),
'data': parsed_rows
}
save_snapshot(snapshot)


return data


except Exception as e:
print("Fetch Error:", e)
return None
