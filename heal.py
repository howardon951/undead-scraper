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


def get_initial_error() -> str:
    result = subprocess.run(["python", "scraper.py"], capture_output=True, text=True)
    return (result.stdout + result.stderr).strip()


def run_agent(initial_error: str):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    system = """You are a self-healing agent for a Python scraper running in GitHub Actions.

MANDATORY FIRST STEPS — always do this before anything else:
1. Call read_file("skills/index.md") to see the available skills
2. Match the error prefix in the error message to the correct skill
3. Call read_file("skills/<chosen-skill>.md") to get detailed instructions
4. Follow that skill's procedure exactly to diagnose and fix the issue

Rules:
- Only modify config.json. Never modify scraper.py or other files.
- Always verify your fix by running python scraper.py before finishing.
- The fix is complete only when scraper.py exits 0 and prints SUCCESS."""

    messages = [
        {
            "role": "user",
            "content": (
                f"The scraper GitHub Actions workflow just failed.\n\n"
                f"Initial error output:\n```\n{initial_error}\n```\n\n"
                f"Please read skills/index.md first, select the right skill, "
                f"then diagnose and fix the issue."
            ),
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
    result = subprocess.run(["python", "scraper.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Scraper still failing:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    print("✓ Scraper passing — ready to commit")


if __name__ == "__main__":
    print("=== Pre-run: capturing initial error ===")
    initial_error = get_initial_error()
    print(initial_error)

    if "SUCCESS" in initial_error:
        print("Scraper already passing — nothing to fix.")
        sys.exit(0)

    print()
    run_agent(initial_error)
