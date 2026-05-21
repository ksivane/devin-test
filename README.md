# Devin take home assignment - PR Reviewer for ksivane github repo

This script automates the process of reviewing GitHub Pull Requests using Devin AI. It monitors ksivane repository for new open PRs, triggers a Devin session to perform a structured code review, and displays the results—including summaries, actions taken, and security concerns—directly in your terminal.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd devin
    ```

2.  **Install dependencies**:
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Environment variables**:
    The script already has devin api keys. Note, this is temporary one which will expire/be deleted.
    A valid Github token may need to be provided for ksivane repo if 403 error is seen.

2.  **Run the script**:
    ```bash
    python devin-pr.py
    ```

The script will start monitoring the ksivane repository for new PRs. Once a new PR is detected, Devin will begin its review.
