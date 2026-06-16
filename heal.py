import json
import os
import subprocess
import sys

import anthropic

MAX_TURNS = 15

TOOLS = [
    {
        "name": "run_command",
        "description": "Run a shell command. Returns stdout + stderr combined.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"}
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file from the repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to repo root"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
]


def execute_tool(name: str, inputs: dict) -> str:
    if name == "run_command":
        result = subprocess.run(
            inputs["command"], shell=True, capture_output=True, text=True
        )
        output = (result.stdout + result.stderr).strip()
        print(f"  $ {inputs['command'][:80]}")
        print(f"  → {output[:300]}")
        return output or "(no output)"

    if name == "read_file":
        path = inputs["path"]
        print(f"  read_file({path})")
        try:
            return open(path).read()
        except FileNotFoundError:
            return f"ERROR: file not found: {path}"

    if name == "write_file":
        path = inputs["path"]
        print(f"  write_file({path})")
        with open(path, "w") as f:
            f.write(inputs["content"])
        return f"Written: {path}"

    return f"ERROR: unknown tool {name}"


def get_initial_context() -> dict:
    """Run scraper + inspector and collect all available context."""
    scraper_result = subprocess.run(["python", "scraper.py"], capture_output=True, text=True)
    scraper_output = (scraper_result.stdout + scraper_result.stderr).strip()

    inspect_result = subprocess.run(["python", "inspect.py"], capture_output=True, text=True)
    inspect_output = (inspect_result.stdout + inspect_result.stderr).strip()

    inspect_report = ""
    try:
        inspect_report = open("inspect_report.txt").read()
    except FileNotFoundError:
        pass

    output_sample = ""
    try:
        data = json.load(open("output.json"))
        output_sample = json.dumps({
            "result_count": data["result_count"],
            "field_stats": data["field_stats"],
            "sample": data["results"][:2],
        }, indent=2)
    except FileNotFoundError:
        pass

    return {
        "scraper_output": scraper_output,
        "inspect_output": inspect_output,
        "inspect_report": inspect_report,
        "output_sample": output_sample,
        "crashed": scraper_result.returncode != 0,
        "drift_detected": inspect_result.returncode != 0,
    }


def build_initial_message(ctx: dict) -> str:
    parts = ["The scraper GitHub Actions workflow just failed.\n"]

    if ctx["crashed"]:
        parts.append(f"**Scraper crashed:**\n```\n{ctx['scraper_output']}\n```\n")
    else:
        parts.append(f"**Scraper ran successfully but data quality check failed.**\n")
        parts.append(f"Scraper output:\n```\n{ctx['scraper_output']}\n```\n")

    if ctx["inspect_report"]:
        parts.append(f"**Inspector report:**\n```\n{ctx['inspect_report']}\n```\n")
    elif ctx["inspect_output"]:
        parts.append(f"**Inspector output:**\n```\n{ctx['inspect_output']}\n```\n")

    if ctx["output_sample"]:
        parts.append(f"**Scraped data sample:**\n```json\n{ctx['output_sample']}\n```\n")

    parts.append("Please read skills/index.md first, select the right skill, then diagnose and fix the issue.")
    return "\n".join(parts)


def run_agent(ctx: dict):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    system = """You are a self-healing agent for a Python scraper running in GitHub Actions.
Your goal is data fidelity — the scraped output must accurately reflect what the real world contains.

You handle two types of failures:
1. CRASH: scraper.py exited non-zero (broken selector, wrong URL, timeout, schema error)
2. DRIFT: scraper.py succeeded but inspect.py detected data quality issues
   (low fill rate, fields disappearing, result count dropping)
   This means the real world changed — the site's HTML structure evolved.

MANDATORY FIRST STEPS — always do this before anything else:
1. Call read_file("skills/index.md") to understand available skills
2. Reason about the nature of the failure and select the most appropriate skill
3. Call read_file("skills/<chosen-skill>.md") for detailed instructions
4. Follow that skill's diagnostic and repair procedure

Rules:
- Only modify config.json. Never modify scraper.py, inspect.py, or other files.
- For drift failures: your job is to update the schema to match current reality,
  not to restore a previous state. The real world is the source of truth.
- Verification must pass BOTH: python scraper.py (exit 0) AND python inspect.py (exit 0).

FINAL STEP — after both verifications pass, write a descriptive commit message:
  write_file(".commit_msg", "fix(<scope>): <what drifted and how schema was updated> [skip ci]")
  Examples:
    fix(schema): update required_fields to match available site fields after HTML restructure [skip ci]
    fix(selectors): update author selector from .author to .author-title after site redesign [skip ci]
    fix(url): restore base URL — path /page/99 no longer exists [skip ci]
  The message must describe what actually changed in the real world, not just what file was edited."""

    messages = [
        {
            "role": "user",
            "content": build_initial_message(ctx),
        }
    ]

    print("=== Agent loop started ===\n")

    for turn in range(MAX_TURNS):
        print(f"--- Turn {turn + 1}/{MAX_TURNS} ---")

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        for block in response.content:
            if hasattr(block, "text") and block.text.strip():
                print(f"Claude: {block.text}")

        if response.stop_reason == "end_turn":
            print("\n=== Agent finished ===")
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\nTool: {block.name}")
                result = execute_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    else:
        print(f"ERROR: hit max turns ({MAX_TURNS})", file=sys.stderr)
        sys.exit(1)

    print("\n=== Final verification ===")
    scraper = subprocess.run(["python", "scraper.py"], capture_output=True, text=True)
    print(scraper.stdout)
    if scraper.returncode != 0:
        print(f"Scraper still failing:\n{scraper.stderr}", file=sys.stderr)
        sys.exit(1)

    inspector = subprocess.run(["python", "inspect.py"], capture_output=True, text=True)
    print(inspector.stdout)
    if inspector.returncode != 0:
        print(f"Data quality still failing:\n{inspector.stderr}", file=sys.stderr)
        sys.exit(1)

    print("✓ Scraper and inspector both passing — ready to commit")


if __name__ == "__main__":
    print("=== Pre-run: collecting context ===")
    ctx = get_initial_context()
    print(ctx["scraper_output"])
    if ctx["inspect_output"]:
        print(ctx["inspect_output"])

    if not ctx["crashed"] and not ctx["drift_detected"]:
        print("Scraper and inspector both passing — nothing to fix.")
        sys.exit(0)

    print()
    run_agent(ctx)
