# Tools

Each script in this directory performs one deterministic task. Scripts are called by the agent following a workflow SOP.

## Naming Convention

`verb_noun.py` — e.g., `scrape_single_site.py`, `export_to_sheets.py`, `parse_json.py`

## Script Structure

Every tool should follow this pattern:

```python
#!/usr/bin/env python3
"""One-line description of what this tool does."""

import argparse
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="...")
    args = parser.parse_args()

    # --- do the work ---

    print("result or status message")  # stdout for the agent to read
    sys.exit(0)  # 0 = success, non-zero = failure

if __name__ == "__main__":
    main()
```

## Conventions

- **Inputs:** via CLI args (`argparse`). No interactive prompts.
- **Outputs:** Write files to `.tmp/` or push to a cloud service. Print a status/result summary to stdout.
- **Errors:** Print a clear error message to stderr and exit non-zero. Never silently fail.
- **Credentials:** Load from `.env` via `python-dotenv`. Never hardcode keys.
