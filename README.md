# Self-Healing Scraper POC

A minimal demonstration of a self-healing GitHub Actions workflow.
When the scraper breaks, a second workflow auto-triggers, runs Claude to diagnose the failure, fixes the CSS selectors, and commits directly back to main — zero human intervention.

## How it works

```
push / workflow_dispatch
        ↓
  [ scraper.yml ] → python scraper.py
        │  exit 1 (0 results found)
        ↓
  [ self-heal.yml ] (workflow_run trigger)
        ↓
  claude-code-action
        ↓
  Claude: read → run → inspect HTML → fix config.json → verify → git push
```

## One-time setup

1. Push this repo to GitHub (both workflow files must land on `main` in the same push for `workflow_run` to register).

2. Add your Anthropic API key as a repo secret:
   **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `ANTHROPIC_API_KEY`
   - Value: your key from [console.anthropic.com](https://console.anthropic.com)

## Test: happy path

Go to **Actions → Scraper → Run workflow**.
Should complete green with output: `SUCCESS: scraped 10 quotes`

## Test: break it and watch it heal

1. Edit `config.json` — change `".quote"` to `".wrong-item"` and `".text"` to `".wrong-text"`
2. Commit directly to `main` and push
3. **Scraper** fails (red ✗)
4. ~30 seconds later **Self-Heal Scraper** auto-triggers
5. Claude runs for ~2–4 minutes, then commits:
   `fix(scraper): auto-repair CSS selectors [skip ci]`
6. Check `main` — `config.json` selectors are restored
7. Manually re-run **Scraper** to confirm green ✓

## Files

| File | Purpose |
|------|---------|
| `scraper.py` | Scraper; raises `ValueError` + exits 1 when 0 results |
| `config.json` | CSS selectors — the intentionally breakable config |
| `requirements.txt` | `requests` + `beautifulsoup4` |
| `.github/workflows/scraper.yml` | Runs the scraper |
| `.github/workflows/self-heal.yml` | Triggers Claude on failure |

## Cost estimate

Each self-healing run: ~$0.25 (Sonnet 4.6, ~30K tokens) + ~$0.06 (Actions minutes) = **~$0.31 per fix**

## Notes

- **`[skip ci]`** in Claude's commit message prevents the healed commit from re-triggering an infinite loop.
- `GITHUB_TOKEN` with `contents: write` (set in `self-heal.yml`) is sufficient for pushing to main. No PAT needed.
- Public repos get free Actions minutes. Private repos use the free tier (2,000 min/month on Free plan).
