import json
import sys

FILL_RATE_THRESHOLD = 0.8  # field must be populated in >= 80% of results


def inspect():
    try:
        output = json.load(open("output.json"))
    except FileNotFoundError:
        print("INSPECT_ERROR: output.json not found — scraper must have crashed before writing", file=sys.stderr)
        sys.exit(1)

    config = json.load(open("config.json"))
    results = output["results"]
    field_stats = output.get("field_stats", {})
    min_results = config.get("min_results", 1)
    required_fields = config.get("required_fields", [])

    issues = []

    # 1. Result count dropped significantly
    if len(results) < min_results:
        issues.append(
            f"result count is {len(results)}, expected >= {min_results}"
        )

    # 2. Required fields have low fill rate (structural drift)
    for field in required_fields:
        stats = field_stats.get(field, {})
        fill_rate = stats.get("fill_rate", 0.0)
        empty = stats.get("empty_count", len(results))
        if fill_rate < FILL_RATE_THRESHOLD:
            issues.append(
                f"field '{field}' fill rate is {fill_rate:.0%} "
                f"({empty}/{len(results)} results empty) — "
                f"selector may have drifted from site HTML"
            )

    # 3. Any field in config schema is entirely absent from scraped data
    scraped_fields = set(field_stats.keys())
    for field in required_fields:
        if field not in scraped_fields:
            issues.append(
                f"field '{field}' does not exist in scraped output at all — "
                f"available fields: {sorted(scraped_fields)}"
            )

    if issues:
        report = "DATA_QUALITY_ERROR: " + "; ".join(issues)
        print(report, file=sys.stderr)
        # Write report for the heal agent to read
        with open("inspect_report.txt", "w") as f:
            f.write(report + "\n\n")
            f.write("Field stats:\n")
            for field, stats in field_stats.items():
                f.write(f"  {field}: {stats}\n")
            f.write(f"\nSample results (first 3):\n")
            for r in results[:3]:
                f.write(f"  {r}\n")
        sys.exit(1)

    print(
        f"QUALITY OK: {len(results)} results — "
        + ", ".join(f"{f}: {field_stats[f]['fill_rate']:.0%}" for f in required_fields if f in field_stats)
    )


if __name__ == "__main__":
    inspect()
