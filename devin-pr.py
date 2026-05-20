import os
import time
import json
import requests

API_KEY = os.getenv("DEVIN_API_KEY", "cog_p34rqfkgpdqdykcmpgme6pchlv3akyrmfmpnq7tqeypgambrt55q")
ORG_ID = os.getenv("DEVIN_ORG_ID", "org-89be989e97a94b09843490de4d71b06b")  # required for v3
BASE_URL = "https://api.devin.ai"
PR_URL = "https://github.com/apache/superset/pull/40274"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# JSON Schema (Draft 7), self-contained, <= 64KB
SCHEMA = {
    "type": "object",
    "properties": {
        "PR status": {
            "type": "string",
            "description": "Whether the PR is open, closed, merged, draft, etc.",
        },
        "Summary": {
            "type": "string",
            "description": "A short explanation of the PR.",
        },
        "Details": {
            "type": "string",
            "description": "Detailed review of the PR.",
        },
        "Security": {
            "type": "string",
            "description": "Any security/vulnerability concerns this PR may cause.",
        },
    },
    "required": ["PR status", "Summary", "Details", "Security"],
    "additionalProperties": False,
}

PROMPT = (
    f"Please review the following GitHub pull request and produce a code review:\n\n"
    f"{PR_URL}\n\n"
    "Fetch the PR, inspect the diff and discussion, and return your findings as "
    "structured JSON matching the provided schema. Fields:\n"
    "- 'PR status': current state of the PR (open/closed/merged/draft).\n"
    "- 'Summary': a short explanation of what the PR does.\n"
    "- 'Details': a detailed review (correctness, design, tests, edge cases).\n"
    "- 'Security': any security or vulnerability concerns introduced by this PR."
)

def create_session():
    url = f"{BASE_URL}/v3/organizations/{ORG_ID}/sessions"
    payload = {
        "prompt": PROMPT,
        "title": "PR review: superset#40274",
        "structured_output_schema": SCHEMA,
        "structured_output_required": True,
    }
    r = requests.post(url, headers=HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()

def get_session(devin_id):
    url = f"{BASE_URL}/v3/organizations/{ORG_ID}/sessions/{devin_id}"
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()

def is_terminal(status, status_detail):
    # v3: status 'exit' or 'error' are terminal. 'suspended' is also effectively done
    # (often with reasons like 'finished' / 'inactivity' / 'usage_limit_exceeded').
    if status in {"exit", "error"}:
        return True
    if status == "suspended":
        return True
    if status == "running" and status_detail == "finished":
        return True
    return False

def poll_until_done(devin_id, interval=15, timeout=60 * 60):
    start = time.time()
    last = None
    while time.time() - start < timeout:
        data = get_session(devin_id)
        status = data.get("status")
        detail = data.get("status_detail")
        key = (status, detail)
        elapsed = int(time.time() - start)
        if key != last:
            print(f"[{elapsed:4d}s] status={status} detail={detail}")
            last = key
        else:
            print(f"[{elapsed:4d}s] still status={status} detail={detail}...")
        if is_terminal(status, detail):
            return data
        time.sleep(interval)
    raise TimeoutError("Session did not finish within timeout.")

def main():
    print("Creating Devin session (v3)...")
    created = create_session()
    devin_id = created["session_id"]
    print(f"Session created: {devin_id}")
    print(f"URL: {created.get('url')}\n")

    print("Polling for completion...")
    final = poll_until_done(devin_id)

    print("\n=== Session finished ===")
    structured = final.get("structured_output")
    if structured:
        print("\nStructured review:\n")
        print(json.dumps(structured, indent=2))
    else:
        print("No structured_output returned.")
        print(f"Final status: {final.get('status')} / {final.get('status_detail')}")

if __name__ == "__main__":
    main()