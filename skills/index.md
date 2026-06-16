# Healing Agent Skill Index

You are a self-healing agent. Before diagnosing any issue, read this index
and select the most appropriate skill based on the error message.

## How to select a skill

Match the error prefix in the error output:

| Error prefix | Skill file | Description |
|---|---|---|
| `CSS_SELECTOR_ERROR` | `skills/css-selector-fix.md` | CSS selectors in config.json don't match the target site's HTML |
| `HTTP_ERROR` | `skills/url-fix.md` | Target URL returns a non-200 HTTP status code |
| `TIMEOUT_ERROR` | `skills/timeout-fix.md` | Request times out — timeout value is too low or site is slow |
| `SCHEMA_ERROR` | `skills/data-schema-fix.md` | Scraped data is missing fields listed in required_fields |

## What to do

1. Identify the error prefix from the error message
2. Read the corresponding skill file using read_file
3. Follow the skill's diagnostic and repair procedure exactly
4. Only modify config.json — never modify scraper.py

If the error does not match any prefix, read all skill files and use
your best judgment.
