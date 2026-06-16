# Skill: CSS Selector Fix

## Trigger
Error prefix: `CSS_SELECTOR_ERROR`

Example:
```
CSS_SELECTOR_ERROR: selector '.broken-container' matched 0 elements, expected >= 1
```

## Background
The scraper uses CSS selectors stored in config.json under the "selectors" key.
The target site is https://quotes.toscrape.com.

The three selectors needed are:
- `quote_container`: outer div wrapping each individual quote
- `quote_text`: element containing the quote text
- `quote_author`: element containing the author name

## Diagnostic procedure

1. Run `python scraper.py` to confirm the exact selector that failed.

2. Fetch the live HTML and inspect the structure:
```
python3 -c "
import requests
from bs4 import BeautifulSoup
r = requests.get('https://quotes.toscrape.com', timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')
# Print the first quote block to see structure
blocks = soup.find_all('div')[5:15]
for b in blocks:
    print(b.prettify()[:500])
    print('---')
"
```

3. Identify the correct class names from the HTML output.

## Repair procedure

Update ONLY the "selectors" object in config.json with the correct values.
Do not change any other field.

## Verification

Run `python scraper.py` — must output `SUCCESS: scraped N quotes` and exit 0.

## Known good selectors for quotes.toscrape.com
```json
{
  "quote_container": ".quote",
  "quote_text": ".text",
  "quote_author": ".author"
}
```
