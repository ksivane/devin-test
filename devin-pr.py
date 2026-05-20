import os
import time
import json
import requests

API_KEY = os.getenv("DEVIN_API_KEY", "cog_p34rqfkgpdqdykcmpgme6pchlv3akyrmfmpnq7tqeypgambrt55q")
ORG_ID = os.getenv("DEVIN_ORG_ID", "org-89be989e97a94b09843490de4d71b06b")  # required for v3
BASE_URL = "https://api.devin.ai"
PR_URL = "https://github.com/ksivane/devin-superset/pull/8"

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
        "Actions": {
            "type": "string",
            "description": "A short explanation of actions taken by you.",
        },
        "Security": {
            "type": "string",
            "description": "Any security/vulnerability concerns this PR may cause.",
        },
    },
    "required": ["PR status", "Summary", "Actions", "Security"],
    "additionalProperties": False,
}

PROMPT = (
    f"When given a GitHub pull request, produce a code review:\n\n"
    "Fetch the PR, inspect the diff and return your findings as "
    "structured JSON matching the provided schema. Fields:\n"
    "- 'PR status': current state of the PR (open/closed/merged/draft).\n"
    "- 'Summary': a short explanation of what the PR does.\n"
    "- 'Actions': a short explanation of actions taken by you on the PR.\n"
    "- 'Security': any security or vulnerability concerns introduced by this PR.\n\n"
    f"Review need not be detailed, just a cursory review for obvious issues is good enough.\n\n"
    f"You are just reviewing a PR, not setting up the repo for development. Fetch the actual diff of the PR instead. You don't need to set up pre-commit hooks since you are not making commits.\n\n"
    f"Dont review PR comments.\n\n"
    f"Further instructions on how to handle PRs:\n"
    f"- If secrets leakage is found (e.g. Passwords, API keys), redact them in a new commit and continue. Also add a appropriate comment in code to denote the redaction. Start comment with \"Devin AI\"\n"
    f"- If not other issues that require human input, create a new PR if needed and close the original.\n"
    f"- Add explict PR comments too indicating it was done by \"Devin AI\"\n"
)
PROMPT_PR_URL = f"\n\nPR: {PR_URL}\n\n"


def create_session():
    url = f"{BASE_URL}/v3/organizations/{ORG_ID}/sessions"
    payload = {
        "prompt": PROMPT + PROMPT_PR_URL,
        "title": "PR review: superset",
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
    if status in {"exit", "error", "suspended"}:
        return True
    if status_detail in {"finished", "waiting_for_user"}:
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

def resume_session(devin_id):
    url = f"{BASE_URL}/v3/organizations/{ORG_ID}/sessions/{devin_id}/messages"
    payload = {"message": PROMPT_PR_URL}
    r = requests.post(url, headers=HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    return get_session(devin_id)

def main():
    # 1. Look for session id in environment or use hardcoded one.
    script_start_time = time.time()
    devin_id = os.environ.get("DEVIN_SESSION_ID", "a9e7fdfdab2f473784542770c107c0ad") # e6c1a8edfce74a4a9f2716e238c18602

    try:
        print(f"Attempting to resume session {devin_id}...")
        session = resume_session(devin_id)
        print(f"Resumed: {devin_id}")
    except Exception as e:
        print(f"Resume failed ({e}); creating new session.")
        session = create_session()
        devin_id = session["session_id"]
        print(f"Created: {devin_id}")

    start_ts = session["created_at"]
    print(f"URL: {session.get('url')}\n")

    print("Polling for completion...")
    final = poll_until_done(devin_id)

    print("\n=== Session finished ===")
    structured = final.get("structured_output")
    print(final)
    if structured:
        print("\nStructured review:\n")
        print(json.dumps(structured, indent=2))
    else:
        print("No structured_output returned.")
        print(f"Final status: {final.get('status')} / {final.get('status_detail')}")

    # Session summary matching devin-session.py
    print("\n--- Session summary ---")
    print(f"Session ID:    {final['session_id']}")
    print(f"Final status:  {final['status']} ({final.get('status_detail')})")
    print(f"ACUs consumed: {final['acus_consumed']}")
    print(f"Elapsed:       {int(time.time() - script_start_time)}s")
    print(f"URL:           {final['url']}")

if __name__ == "__main__":
    main()


f"Review this: https://github.com/ksivane/devin-superset/pull/6\n"
