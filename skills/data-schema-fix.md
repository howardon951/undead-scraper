# Skill: Data Schema Fix

## Trigger
Error prefix: `SCHEMA_ERROR`

Example:
```
SCHEMA_ERROR: required field 'link' is missing or empty in 10/10 results.
Available fields: ['text', 'author']
```

## Background
The scraper validates that every scraped result contains the fields listed in
config.json's "required_fields" array. If a field is listed there but is not
actually scraped by scraper.py, the validation fails.

The scraper currently extracts exactly two fields per quote:
- `text`: the quote body
- `author`: the author name

No other fields are extracted.

## Diagnostic procedure

1. Read the current config.json to see what fields are in required_fields.

2. Check what fields the scraper actually produces:
```
python3 -c "
import json, requests
from bs4 import BeautifulSoup
cfg = json.load(open('config.json'))
r = requests.get(cfg['url'], timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')
item = soup.select(cfg['selectors']['quote_container'])[0]
text_el = item.select_one(cfg['selectors']['quote_text'])
author_el = item.select_one(cfg['selectors']['quote_author'])
result = {
    'text': text_el.get_text(strip=True) if text_el else '',
    'author': author_el.get_text(strip=True) if author_el else '',
}
print('Fields actually available:', list(result.keys()))
print('Sample:', result)
"
```

3. Compare the available fields with required_fields to identify the mismatch.

## Repair procedure

Update ONLY the "required_fields" array in config.json.
Remove any fields that are not in the list of actually available fields.
Only keep fields that are confirmed to exist in the scraped data.

## Verification

Run `python scraper.py` — must output `SUCCESS: scraped N quotes` and exit 0.

## Valid required_fields for this scraper
```json
{
  "required_fields": ["text", "author"]
}
```
