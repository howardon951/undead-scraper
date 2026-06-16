# Skill: Schema Evolution

## When to use this skill
The scraper ran successfully (exit 0, scraped data) but the data quality
inspector detected drift: required fields have low fill rates, fields are
missing entirely, or result counts dropped unexpectedly.

This means the real world changed — the site's HTML structure evolved, fields
moved, or content is now organized differently. The schema in config.json no
longer reflects what the site actually provides.

**The real world is the source of truth. Update the schema to match it.**

## Background
config.json defines what fields to extract and which are required:
- `selectors`: CSS selectors for each field
- `required_fields`: fields that must be non-empty in every result
- `min_results`: minimum number of results expected

When the site changes its HTML, selectors may still find elements but those
elements may now be empty, structured differently, or moved to new locations.

## Diagnostic procedure

1. Read the inspector report to understand what specifically drifted:
```
read_file("inspect_report.txt")
```

2. Read current config.json to see what schema we expect:
```
read_file("config.json")
```

3. Fetch the live site and discover what fields are actually available now:
```
python3 -c "
import requests, json
from bs4 import BeautifulSoup
cfg = json.load(open('config.json'))
r = requests.get(cfg['url'], timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')
containers = soup.select(cfg['selectors']['quote_container'])
print(f'Found {len(containers)} containers with selector: {cfg[\"selectors\"][\"quote_container\"]}')
if containers:
    item = containers[0]
    print('--- First container HTML ---')
    print(item.prettify()[:800])
    print('--- All child element classes ---')
    for el in item.find_all(True):
        print(f'  <{el.name}> class={el.get(\"class\")} text={el.get_text(strip=True)[:40]}')
"
```

4. Identify all fields that ARE actually available in the real HTML.
   Discover what's extractable — don't limit yourself to existing selectors.

5. Compare: what does the schema currently require vs. what actually exists?
   - Fields that disappeared: remove from required_fields or update selectors
   - Fields that moved: update the selector
   - New fields that appeared: consider adding to schema

## Repair procedure

Update config.json to reflect current reality:
- Fix any selectors that now point to empty/wrong elements
- Remove fields from `required_fields` that the site no longer provides
- Add new fields to `required_fields` if they are now stable and useful
- Only keep a field as required if it has >= 80% fill rate in the real data

## Verification

Both must pass:
1. `python scraper.py` — must print `SUCCESS: scraped N quotes` and exit 0
2. `python inspect.py` — must print `QUALITY OK` and exit 0

## If fix fails

If inspect.py still reports drift after updating the schema:
1. Re-run the diagnostic — the site may have both selector AND schema issues.
   Fix selectors first, then re-check fill rates.
2. A field may exist in HTML but be empty for many results — this is genuine
   data sparsity, not a bug. Lower the threshold by removing it from required_fields.
3. If result count dropped: check if the container selector is still finding
   the right elements. The site may have restructured its layout entirely.
4. Run the full diagnostic again from scratch — sometimes one fix reveals
   a second underlying issue.
