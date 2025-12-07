import requests




def get_nse_session():
"""Create a requests.Session with headers and attempt to warm cookies by visiting the homepage.
Note: this improves the chance of a successful API call but is not guaranteed.
"""
session = requests.Session()
headers = {
"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
"Accept": "application/json, text/javascript, */*; q=0.01",
"Accept-Language": "en-US,en;q=0.9",
"Referer": "https://www.nseindia.com",
}


session.headers.update(headers)


try:
session.get("https://www.nseindia.com", timeout=5)
except Exception:
# ignore errors — caller will handle
pass
return session
