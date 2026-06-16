# Skill: CSS Selector Fix

## When to use this skill
The page loads with HTTP 200, but the CSS selectors in config.json do not
match any elements in the HTML. The scraper finds 0 results even though
the site is reachable.

## Background
The scraper uses three CSS selectors from config.json:
- `quote_container`: outer element wrapping each item
- `quote_text`: element containing the main text
- `quote_author`: element containing the author name

All three must match elements that actually exist in the page HTML.

## Diagnostic procedure

1. Run `python scraper.py` to confirm the exact failing selector.

2. Fetch the live page and inspect the structure around quotes:
```
python3 -c "
import requests, json
from bs4 import BeautifulSoup
cfg = json.load(open('config.json'))
r = requests.get(cfg['url'], timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')
# Print a sample of the body to find the real structure
print(r.text[2000:6000])
"
```

3. From the HTML output, identify:
   - Which element wraps each quote block (look for repeated patterns)
   - Which child element holds the quote text
   - Which child element holds the author name

4. Confirm your selectors actually work before writing:
```
python3 -c "
import requests, json
from bs4 import BeautifulSoup
cfg = json.load(open('config.json'))
r = requests.get(cfg['url'], timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')
# Test your candidate selector here
items = soup.select('YOUR_SELECTOR_HERE')
print(f'Found {len(items)} items')
if items:
    print(items[0].prettify()[:400])
"
```

## Repair procedure

Update ONLY the `selectors` object in config.json with selectors confirmed
to return results in step 4.

## Verification

Run `python scraper.py` — must print `SUCCESS: scraped N quotes` and exit 0.

## If fix fails

If verification still fails after updating selectors:
1. Your selectors may be partially wrong — re-examine the HTML more carefully.
   Print a larger range: `r.text[0:8000]` to see more context.
2. Test each selector independently before combining all three.
3. The container selector is the most important — get that right first,
   then find text and author within it.
4. Try attribute selectors or tag-based selectors if class names are not clear.
5. If `len(items) > 0` in step 4 but scraper still fails, check that
   `quote_text` and `quote_author` exist as children of `quote_container`.
