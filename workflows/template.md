# Workflow: [Name]

> Copy this file and rename it for each new workflow. Fill in every section before running.

## Objective

What this workflow accomplishes in one sentence.

## Inputs

| Input | Description | Example |
|-------|-------------|---------|
| `input_name` | What it is | `"example value"` |

## Steps

1. **[Step name]**
   - Tool: `tools/tool_name.py`
   - Command: `python tools/tool_name.py --input "{{input_name}}"`
   - Output: Describe what the tool produces (file path, stdout, cloud service)

2. **[Next step]**
   - Tool: `tools/another_tool.py`
   - Command: `python tools/another_tool.py --input ".tmp/output_from_step_1.json"`
   - Output: ...

## Expected Output

Describe the final deliverable: file location, Google Sheet URL, format, etc.

## Edge Cases & Known Issues

- **Rate limits:** e.g., "API allows 10 req/min — tool handles backoff automatically"
- **Auth errors:** e.g., "If Google auth fails, delete `token.json` and re-run to re-authenticate"
- **Empty results:** e.g., "If scrape returns nothing, check that the URL is publicly accessible"

## Notes

Any context, quirks, or lessons learned from running this workflow.
