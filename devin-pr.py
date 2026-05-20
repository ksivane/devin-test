import os
import time
import json
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.status import Status
from rich.json import JSON
from rich.theme import Theme

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green",
    "faded": "grey50",
})

console = Console(theme=custom_theme)

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
        "NewPR": {
            "type": "string",
            "description": "URL of any new PR created as a result of this review or original PR",
        }
    },
    "required": ["PR status", "Summary", "Actions", "Security", "NewPR"],
    "additionalProperties": False,
}

PROMPT = (
    f"When given a GitHub pull request, produce a code review:\n\n"
    "Fetch the PR, inspect the diff and return your findings as "
    "structured JSON matching the provided schema. Be terse when filling the fields. Fields:\n"
    "- 'PR status': current state of the PR (open/closed/merged/draft).\n"
    "- 'Summary': a short explanation of what the PR does.\n"
    "- 'Actions': a short explanation of actions taken by you on the PR.\n"
    "- 'NewPR': URL of any new PR created as a result of this review or original PR.\n"
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
    with console.status("[faded]Devin AI is working...[/faded]", spinner="dots") as status_indicator:
        while time.time() - start < timeout:
            data = get_session(devin_id)
            status = data.get("status")
            detail = data.get("status_detail")
            key = (status, detail)
            elapsed = int(time.time() - start)

            msg = f"[faded][{elapsed:4d}s][/faded] status=[bold cyan]{status}[/bold cyan] detail=[bold blue]{detail}[/bold blue]"
            if key != last:
                console.log(f"[faded]Devin AI is working...[/faded] {msg}")
                last = key

            status_indicator.update(f"[faded]Devin AI is working...[/faded] {msg}")

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
    devin_id = os.environ.get("DEVIN_SESSION_ID", "d43e007272cd42e6bc41b012996f6bc9")

    console.print(Panel(f"Devin AI will now review PR: [bold blue]{PR_URL}[/bold blue]", border_style="green"))

    try:
        console.print(f"[faded]Attempting to resume session {devin_id}...[/faded]")
        session = resume_session(devin_id)
        console.print(f"[faded]Resumed session: {devin_id}[/faded]")
    except Exception as e:
        console.print(f"[faded]Resume failed ({e}); creating new session.[/faded]")
        session = create_session()
        devin_id = session["session_id"]
        console.print(f"[faded]Created new session: {devin_id}[/faded]")

    console.print(f"[faded]URL: {session.get('url')}[/faded]\n")

    final = poll_until_done(devin_id)

    console.print("\n[bold]=== Session Finished ===[/bold]\n")

    structured = final.get("structured_output")
    if structured:
        content = Table.grid(padding=(0, 1))
        content.add_column(style="bold cyan", justify="right")
        content.add_column()

        content.add_row("PR Status:", structured.get("PR status"))
        content.add_row("Summary:", structured.get("Summary"))
        content.add_row("", "") # Spacer
        content.add_row("Actions:", f"[bold green]{structured.get('Actions')}[/bold green]")
        content.add_row("Security:", f"[bold red]{structured.get('Security')}[/bold red]")

        console.print(Panel(content, title="[bold]Devin Here! This is what i did with the PR[/bold]", expand=False, border_style="blue"))
    else:
        console.print("[danger]No structured_output returned.[/danger]")
        console.print(f"Final status: [bold]{final.get('status')}[/bold] / [bold]{final.get('status_detail')}[/bold]")

    # Session summary - less prominent
    console.print("\n[faded]Technical Session Summary:[/faded]")
    console.print(f"[faded]ID: {final['session_id']} | Status: {final['status']} ({final.get('status_detail')}) | ACUs: {final['acus_consumed']} | Time: {int(time.time() - script_start_time)}s[/faded]")
    console.print(f"[faded]URL: {final['url']}[/faded]\n")

if __name__ == "__main__":
    main()


f"Review this: https://github.com/ksivane/devin-superset/pull/6\n"
