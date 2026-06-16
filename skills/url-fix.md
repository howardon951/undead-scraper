# Skill: URL Fix

## Trigger
Error prefix: `HTTP_ERROR`

Example:
```
HTTP_ERROR: 404 at https://quotes.toscrape.com/this-is-broken/
```

## Background
The scraper fetches the URL stored in config.json under the "url" key.
A non-200 HTTP response means the URL is wrong — the page does not exist
or has moved.

The correct base URL for the target site is: https://quotes.toscrape.com

## Diagnostic procedure

1. Read config.json to see the current URL.

2. Try fetching the current URL to confirm the HTTP error:
```
python3 -c "
import requests
import json
cfg = json.load(open('config.json'))
r = requests.get(cfg['url'], timeout=15)
print(f'Status: {r.status_code}')
print(f'URL: {r.url}')
"
```

3. Try the canonical base URL to confirm it works:
```
python3 -c "
import requests
r = requests.get('https://quotes.toscrape.com', timeout=15)
print(f'Status: {r.status_code}')
"
```

## Repair procedure

Update ONLY the "url" field in config.json to the working URL.

## Verification

Run `python scraper.py` — must output `SUCCESS: scraped N quotes` and exit 0.

## Known good URL
```json
{
  "url": "https://quotes.toscrape.com"
}
```
