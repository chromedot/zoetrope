import json
import random
import urllib.request
import urllib.parse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 1. Load the last run data
try:
    with open('last_run.json', 'r') as f:
        prompt_data = json.load(f)
except FileNotFoundError:
    print("Error: last_run.json not found. This script requires a previous run to be captured.")
    exit(1)

# The API format from history returns [row_id, node_id, prompt_json, extra_data]
# We only need the prompt_json (index 2)
api_payload = prompt_data[2]

...

# 4. Save to file for the user
with open(PROJECT_ROOT / 'workflows' / 'flux_photoreal_api.json', 'w') as f:
    json.dump(api_payload, f, indent=2)

# 5. Submit to API
p = {"prompt": api_payload}
data = json.dumps(p).encode('utf-8')
req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
try:
    response = urllib.request.urlopen(req)
    print("Successfully submitted to Queue!")
    print(response.read().decode('utf-8'))
except Exception as e:
    print(f"Error submitting to API: {e}")
