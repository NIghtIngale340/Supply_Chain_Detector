# GitHub Action Scanner

This custom action scans dependencies in `requirements.txt` and `package.json` by calling the detector API.

## Inputs

- `api_base_url` (default: `http://localhost:8000`)
- `threshold` (default: `70`)
- `poll_timeout` in seconds (default: `90`)

## Example workflow usage

```yaml
name: dependency-scan

on:
  pull_request:
  push:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Supply Chain Detector Action
        uses: ./github_action
        with:
          api_base_url: http://localhost:8000
          threshold: "70"
          poll_timeout: "90"
```
