# Skill: Data Schema Fix

## When to use this skill
The page loaded and content was scraped, but the results are missing fields
declared as required in config.json. The scraper found data but it does not
match the expected schema.

## Background
The scraper validates that every result contains the fields listed in
config.json's `required_fields` array. If a field is listed there but
not actually extracted by scraper.py, validation fails.

## Diagnostic procedure

1. Read config.json to see what fields are currently required.

2. Check what fields the scraper actually produces by running a live test:
```
python3 -c "
import json, requests
from bs4 import BeautifulSoup
cfg = json.load(open('config.json'))
r = requests.get(cfg['url'], timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')
containers = soup.select(cfg['selectors']['quote_container'])
if containers:
    item = containers[0]
    text_el = item.select_one(cfg['selectors']['quote_text'])
    author_el = item.select_one(cfg['selectors']['quote_author'])
    result = {
        'text': text_el.get_text(strip=True) if text_el else None,
        'author': author_el.get_text(strip=True) if author_el else None,
    }
    print('Fields actually available:', [k for k, v in result.items() if v])
    print('Sample result:', result)
else:
    print('No containers found — check selectors first')
"
```

3. Compare the available fields with the `required_fields` in config.json.
   Identify which required fields do not exist in the actual scraped data.

## Repair procedure

Update ONLY the `required_fields` array in config.json. Remove any fields
that are not present in the actual scraped data confirmed in step 2.
Keep only fields that are confirmed to be non-empty in real results.

## Verification

Run `python scraper.py` — must print `SUCCESS: scraped N quotes` and exit 0.

## If fix fails

If validation still fails after updating required_fields:
1. Re-run the diagnostic — some fields may be empty for some results
   even if they exist. Check multiple results, not just the first one.
2. A field may exist but be empty string — this also counts as missing.
   Inspect: `print([r for r in results if not r.get('field_name')])`
3. If the selector for a required field returns nothing, a selector fix
   may also be needed alongside this schema fix.
4. If required_fields is empty `[]`, the validation is skipped entirely —
   this is valid if no field validation is needed.
