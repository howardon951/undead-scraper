# Skill: Timeout Fix

## Trigger
Error prefix: `TIMEOUT_ERROR`

Example:
```
TIMEOUT_ERROR: request timed out after 0.001s connecting to https://quotes.toscrape.com
```

## Background
The scraper uses the "timeout" value from config.json (in seconds) for HTTP requests.
A value that is too low will cause the request to fail before the server responds.

Typical response time for quotes.toscrape.com is under 2 seconds.
A safe timeout value is between 10 and 30 seconds.

## Diagnostic procedure

1. Read config.json to find the current timeout value.

2. Check the current timeout:
```
python3 -c "
import json
cfg = json.load(open('config.json'))
print(f'Current timeout: {cfg.get(\"timeout\", \"not set (default 15)\")}s')
"
```

3. Test connectivity with a generous timeout to confirm the site is reachable:
```
python3 -c "
import requests
r = requests.get('https://quotes.toscrape.com', timeout=30)
print(f'Site reachable: {r.status_code} in {r.elapsed.total_seconds():.2f}s')
"
```

## Repair procedure

Update ONLY the "timeout" field in config.json.
Set it to a value between 15 and 30 seconds.

## Verification

Run `python scraper.py` — must output `SUCCESS: scraped N quotes` and exit 0.

## Recommended value
```json
{
  "timeout": 15
}
```
