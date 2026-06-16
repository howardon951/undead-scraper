import json
import os
import subprocess
import sys

import anthropic

MAX_TURNS = 10

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
        print(f"  $ {inputs['command']}\n  → {output[:300]}")
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


def run_agent():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    system = """You are a self-healing scraper agent. Your job is to fix a broken Python scraper.

You have three tools:
- run_command: run shell commands (python, curl, etc.)
- read_file: read files in the repo
- write_file: write files in the repo

Strategy:
1. Run `python scraper.py` to see the error
2. Read config.json and scraper.py to understand the structure
3. Fetch the target URL HTML to find correct CSS selectors
4. Fix config.json with the correct selectors
5. Run `python scraper.py` again to verify — must print SUCCESS
6. If verification fails, try different selectors and repeat
7. Only stop when the scraper runs successfully

Only modify config.json. Do not touch scraper.py or other files."""

    messages = [
        {
            "role": "user",
            "content": "The scraper GitHub Actions workflow just failed. Please diagnose and fix it.",
        }
    ]

    print("=== Agent loop started ===\n")

    for turn in range(MAX_TURNS):
        print(f"--- Turn {turn + 1}/{MAX_TURNS} ---")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        # Collect any text Claude outputs
        for block in response.content:
            if hasattr(block, "text"):
                print(f"Claude: {block.text}")

        # If Claude is done (no more tool calls)
        if response.stop_reason == "end_turn":
            print("\n=== Agent finished ===")
            break

        # Execute tool calls and collect results
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

        # Append Claude's turn + tool results to conversation
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    else:
        print(f"ERROR: hit max turns ({MAX_TURNS}) without finishing", file=sys.stderr)
        sys.exit(1)

    # Final check: scraper must pass
    print("\n=== Final verification ===")
    result = subprocess.run(["python", "scraper.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Scraper still failing:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    print("✓ Scraper passing — ready to commit")


if __name__ == "__main__":
    run_agent()
