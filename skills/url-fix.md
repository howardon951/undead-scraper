# Skill: URL Fix

## When to use this skill
The HTTP request returned a non-200 status code, or the connection was
refused. The problem is with the URL in config.json, not with parsing.

## Background
The scraper fetches the URL stored in config.json's `url` field. If the
URL is wrong, moved, or does not exist, the request will fail before
any scraping can happen.

## Diagnostic procedure

1. Read config.json to see the current URL.

2. Test the current URL directly:
```
python3 -c "
import requests, json
cfg = json.load(open('config.json'))
r = requests.get(cfg['url'], timeout=15, allow_redirects=True)
print(f'Status: {r.status_code}')
print(f'Final URL after redirects: {r.url}')
print(f'Content-Type: {r.headers.get(\"content-type\", \"unknown\")}')
"
```

3. If that URL fails, try variations to find a working one:
   - Remove path segments one at a time to find the valid base URL
   - Try with and without trailing slash
   - Check if the domain itself is reachable

4. Confirm the working URL actually contains the expected content:
```
python3 -c "
import requests
r = requests.get('CANDIDATE_URL_HERE', timeout=15)
print(f'Status: {r.status_code}')
print(r.text[:1000])
"
```

## Repair procedure

Update ONLY the `url` field in config.json to the working URL you confirmed
in step 4.

## Verification

Run `python scraper.py` — must print `SUCCESS: scraped N quotes` and exit 0.

## If fix fails

If the scraper still fails after updating the URL:
1. The new URL may return 200 but have different HTML structure — check if
   a css-selector-fix is also needed.
2. The site may require specific request headers (User-Agent, cookies).
   Test with: `requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)`
3. Redirect chains may be hiding the real destination — print `r.url` after
   the request to see the final URL.
4. If the domain itself is unreachable, the site may be down. The only fix
   is to find an alternative URL that serves the same content.
