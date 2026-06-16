# Healing Agent Skill Index

You are a self-healing agent. Before doing anything, read this index and
reason about which skill best matches the failure.

## How to select a skill

Do NOT rely on error message prefixes alone. Read the error, think about
the root cause, and pick the skill that matches the nature of the problem.

### skills/css-selector-fix.md
**Use when**: The page loaded successfully (HTTP 200) but no elements were
found matching the CSS selectors. The scraper fetched the HTML but could not
locate the expected content within it.
Signs: "matched 0 elements", "found 0", selector returns empty list.

### skills/url-fix.md
**Use when**: The HTTP request itself failed or returned a non-200 status.
The problem is with the target URL, not with parsing.
Signs: 404, 403, 500, "page not found", "not OK", HTTP status errors.

### skills/timeout-fix.md
**Use when**: The connection or read operation timed out before receiving
a response. The server may be slow or the timeout value is too low.
Signs: "timed out", "ConnectTimeout", "ReadTimeout", "connection failed".

### skills/data-schema-fix.md
**Use when**: The page loaded and content was found, but the scraped results
are missing fields that config.json declares as required. The data structure
does not match what the configuration expects.
Signs: "required field", "missing", "empty in N/N results".

### skills/schema-evolution.md
**Use when**: The scraper ran and returned data, but the data quality inspector
detected drift — fields have low fill rates, required fields are missing, or
result counts dropped. The real world changed; update the schema to match it.
Signs: "DATA_QUALITY_ERROR", "fill rate", "DRIFT", inspect.py exited non-zero.

## If no skill matches

If the error does not clearly match any skill above, read all five skill
files and apply your best judgment. The goal is always to fix config.json
so that BOTH python scraper.py AND python inspect.py exit 0.
