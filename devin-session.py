import os
import time
import requests

API_KEY = os.environ.get("DEVIN_API_KEY", "cog_p34rqfkgpdqdykcmpgme6pchlv3akyrmfmpnq7tqeypgambrt55q")
ORG_ID = os.environ.get("DEVIN_ORG_ID", "org-89be989e97a94b09843490de4d71b06b")  # required for v3
BASE_URL = "https://api.devin.ai"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# 1. Create a new session. The `prompt` field doubles as the first message.
create_resp = requests.post(
    f"{BASE_URL}/v3/organizations/{ORG_ID}/sessions",
    headers=headers,
    json={"prompt": "What is Devin AI?"},
)
create_resp.raise_for_status()
session = create_resp.json()
devin_id = session["session_id"]            # e.g. "devin-abc123"
print(f"Session created: {devin_id}")
print(f"URL:   {session['url']}")
print(f"Status: {session['status']}")
start_ts = session["created_at"]

# 2. Poll for Devin's response (async — no immediate reply).
seen_event_ids = set()
terminal = {"exit", "error", "suspended"}

while True:
    s = requests.get(
        f"{BASE_URL}/v3/organizations/{ORG_ID}/sessions/{devin_id}",
        headers=headers,
    ).json()

    msgs = requests.get(
        f"{BASE_URL}/v3/organizations/{ORG_ID}/sessions/{devin_id}/messages",
        headers=headers,
    ).json()

    for m in msgs.get("items", []):
        if m["source"] == "devin" and m["event_id"] not in seen_event_ids:
            seen_event_ids.add(m["event_id"])
            print(f"\n[Devin] {m['message']}")

    status = s["status"]
    detail = s.get("status_detail")
    print(f"...status={status} detail={detail} acus={s['acus_consumed']:.2f}", end="\r")

    # Stop once Devin is done answering or the session ends.
    if status in terminal or detail in {"finished", "waiting_for_user"}:
        break
    time.sleep(3)

# 3. Useful info from SessionResponse.
print("\n--- Session summary ---")
print(f"Session ID:    {s['session_id']}")
print(f"Final status:  {s['status']} ({s.get('status_detail')})")
print(f"ACUs consumed: {s['acus_consumed']}")          # Devin's usage metric
print(f"Elapsed:       {s['updated_at'] - start_ts}s")
print(f"URL:           {s['url']}")