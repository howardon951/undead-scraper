# Skill: Timeout Fix

## When to use this skill
The HTTP request timed out — the connection could not be established, or
the server did not respond within the allowed time. The timeout value in
config.json may be too low, or the server is genuinely slow.

## Background
The scraper uses the `timeout` value from config.json (in seconds) when
making HTTP requests. A value that is too small causes every request to
fail before the server has time to respond.

## Diagnostic procedure

1. Read config.json to find the current timeout value.

2. Measure the actual response time of the target site:
```
python3 -c "
import requests, json, time
cfg = json.load(open('config.json'))
# Use a generous timeout to measure real response time
start = time.time()
try:
    r = requests.get(cfg['url'], timeout=60)
    elapsed = time.time() - start
    print(f'Site reachable: HTTP {r.status_code} in {elapsed:.2f}s')
except Exception as e:
    elapsed = time.time() - start
    print(f'Failed after {elapsed:.2f}s: {e}')
"
```

3. Compare the measured response time with the current timeout value.
   A safe timeout should be at least 3x the typical response time.

## Repair procedure

Update ONLY the `timeout` field in config.json to a value that comfortably
exceeds the measured response time from step 2. Choose a value that is
safe but not excessively high (avoid values over 60 seconds).

## Verification

Run `python scraper.py` — must print `SUCCESS: scraped N quotes` and exit 0.

## If fix fails

If the scraper still times out after increasing timeout:
1. Try an even larger value — some servers are genuinely slow under load.
2. Test connectivity to the domain at all:
   `python3 -c "import socket; print(socket.gethostbyname('quotes.toscrape.com'))"`
3. If DNS resolution fails, the domain may be unreachable from the CI runner.
4. If the site responds slowly in all tests, the timeout may need to be
   set much higher (30-60 seconds) to handle worst-case server response.
