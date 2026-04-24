#!/usr/bin/env python3
"""
GitHub -> Groq -> Daily Scrum Briefing
---------------------------------------
Fetches your commits and PRs from the last 24 hours across configured repos,
summarises them via Groq, and prints to terminal.

Setup:
  pip install requests groq python-dotenv

Credentials are read from .env in the same directory (or exported env vars):
  GITHUB_TOKEN, GITHUB_USERNAME, GROQ_API_KEY
  REPOS (comma-separated), SCHEDULE, CC

Usage:
  slack_committer                  # Fully AI-generated scrum
  slack_committer --eta            # Prompt for arrival/schedule time
  slack_committer --focus          # Prompt for Today's Focus (AI does sections 1-2)
  slack_committer --eta --focus    # Prompt for both
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from groq import Groq
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass


# -----------------------------------------------
# CONFIG  (all values from .env / environment)
# -----------------------------------------------
def load_config():
    repos_raw = os.environ.get(
        "REPOS",
        "beetleOps/edgevision_mobile,beetleOps/EdgeVision_Core,beetleOps/EdgeVision_WebApp",
    )
    return {
        "github_token":    os.environ.get("GITHUB_TOKEN", ""),
        "github_username": os.environ.get("GITHUB_USERNAME", ""),
        "groq_key":        os.environ.get("GROQ_API_KEY", ""),
        "repos":           [r.strip() for r in repos_raw.split(",") if r.strip()],
        "schedule":        os.environ.get("SCHEDULE", "3:00 pm - 8:00 pm"),
        "cc":              os.environ.get("CC", "@Saad Rana (CTO)"),
        "slack_token":     os.environ.get("SLACK_BOT_TOKEN", ""),
        "slack_user_token": os.environ.get("SLACK_USER_TOKEN", ""),
        "slack_channel":   os.environ.get("SLACK_CHANNEL", "#your-channel-name"),
    }


# -----------------------------------------------
# PROMPTS
# -----------------------------------------------
_RULES = (
    "Rules:\n"
    "- Rewrite raw commit messages as plain English "
    "(e.g. 'fix: auth token null check' -> 'Fixed null token crash in auth')\n"
    "- Section 1 must have 6-8 bullets — group minor related commits into one bullet if there are too many\n"
    "- Do NOT include repo names or commit SHAs in bullets\n"
    "- Do NOT add extra sections, headers, or closing remarks\n"
    "- Output plain text only, no markdown bold or italics"
)

PROMPT_FULL = (
    "You are a helpful assistant that writes concise daily scrum updates "
    "for a software developer.\n\n"
    "Given the GitHub activity below (commits and pull requests from the "
    "last 24 hours), write a scrum update using EXACTLY this format -- "
    "do not add extra sections or change the headings:\n\n"
    "1. Quick Updates (Yesterday's Progress since last sync meet)\n"
    "-  <one bullet per meaningful commit or PR, in plain human language>\n"
    "-  <keep each bullet concise, one line>\n"
    "-  <aim for 6-8 bullets total — group minor related commits into one bullet if needed>\n\n"
    "2. Blockers & Challenges\n"
    "-  <blockers inferred from draft PRs, repeated attempts, or reverts "
    "-- if none write 'None'>\n\n"
    "3. Today's Focus & Next Steps:\n"
    "<one short sentence summarising the likely next steps>\n\n"
    + _RULES
)

PROMPT_NO_FOCUS = (
    "You are a helpful assistant that writes concise daily scrum updates "
    "for a software developer.\n\n"
    "Given the GitHub activity below (commits and pull requests from the "
    "last 24 hours), write ONLY sections 1 and 2 using EXACTLY this format -- "
    "stop after section 2, do NOT write section 3:\n\n"
    "1. Quick Updates (Yesterday's Progress since last sync meet)\n"
    "* <one bullet per meaningful commit or PR, in plain human language>\n"
    "* <keep each bullet concise, one line>\n"
    "* <aim for 6-8 bullets total — group minor related commits into one bullet if needed>\n\n"
    "2. Blockers & Challenges\n"
    "* <blockers inferred from draft PRs, repeated attempts, or reverts "
    "-- if none write 'None'>\n\n"
    + _RULES
)


# -----------------------------------------------
# GITHUB FETCHING
# -----------------------------------------------
REQUEST_TIMEOUT_SECONDS = 15


def build_retry_session():
    session = requests.Session()
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=0.7,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def gh_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def since_timestamp():
    now = datetime.now(timezone.utc)
    lookback = timedelta(days=3) if now.weekday() == 0 else timedelta(hours=24)
    return (now - lookback).isoformat()


def specific_date_window(target_date):
    start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def get_branches(repo, token, session):
    url = f"https://api.github.com/repos/{repo}/branches"
    resp = session.get(
        url,
        headers=gh_headers(token),
        params={"per_page": 100},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if resp.status_code != 200:
        return ["main"]
    return [b["name"] for b in resp.json()]


def fetch_commits(repo, username, token, since, session, until=None):
    branches = get_branches(repo, token, session)
    seen = set()
    results = []
    since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
    until_dt = datetime.fromisoformat(until.replace("Z", "+00:00")) if until else None

    for branch in branches:
        url = f"https://api.github.com/repos/{repo}/commits"
        resp = session.get(
            url, headers=gh_headers(token),
            params={
                "author": username,
                "since": since,
                "until": until,
                "per_page": 50,
                "sha": branch,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if resp.status_code in (409, 403):
            continue
        resp.raise_for_status()
        for c in resp.json():
            if c["sha"] in seen:
                continue
            commit_date = datetime.fromisoformat(
                c["commit"]["author"]["date"].replace("Z", "+00:00")
            )
            if commit_date < since_dt:
                continue
            if until_dt and commit_date >= until_dt:
                continue
            seen.add(c["sha"])
            results.append({
                "repo": repo,
                "type": "commit",
                "sha": c["sha"][:7],
                "message": c["commit"]["message"],
                "date": c["commit"]["author"]["date"],
            })

    return results


def fetch_pull_requests(repo, username, token, since, session, until=None):
    url = f"https://api.github.com/repos/{repo}/pulls"
    results = []
    since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
    until_dt = datetime.fromisoformat(until.replace("Z", "+00:00")) if until else None
    for state in ("open", "closed"):
        resp = session.get(
            url, headers=gh_headers(token),
            params={"state": state, "per_page": 50},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        for pr in resp.json():
            if pr["user"]["login"].lower() != username.lower():
                continue
            updated_at = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
            if updated_at < since_dt:
                continue
            if until_dt and updated_at >= until_dt:
                continue
            results.append({
                "repo": repo,
                "type": "pull_request",
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "draft": pr.get("draft", False),
                "updated_at": pr["updated_at"],
            })
    return results


def collect_activity(config, target_date=None):
    if target_date:
        since, until = specific_date_window(target_date)
        window_label = target_date.strftime("%Y-%m-%d")
    else:
        since = since_timestamp()
        until = None
        window_label = "last 24 hours"

    token = config["github_token"]
    username = config["github_username"]
    activity = []
    session = build_retry_session()
    try:
        for repo in config["repos"]:
            print(f"  Fetching {repo}...")
            try:
                activity += fetch_commits(repo, username, token, since, session, until)
                activity += fetch_pull_requests(repo, username, token, since, session, until)
            except requests.RequestException as e:
                print(f"  Warning: could not fetch {repo}: {e}")
    finally:
        session.close()
    return activity, window_label


def format_activity(activity, window_label="last 24 hours"):
    if not activity:
        return f"No commits or pull requests found for {window_label}."
    lines = []
    for item in activity:
        if item["type"] == "commit":
            lines.append(f"[{item['repo']}] COMMIT {item['sha']}: {item['message']}")
        else:
            tag = "DRAFT PR" if item["draft"] else f"PR ({item['state'].upper()})"
            lines.append(f"[{item['repo']}] {tag} #{item['number']}: {item['title']}")
    return "\n".join(lines)


# -----------------------------------------------
# AI SUMMARISATION
# -----------------------------------------------
def summarise(activity_text, prompt, config, activity_window_label="last 24 hours"):
    client = Groq(api_key=config["groq_key"])
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": (
                f"{prompt}\n\n"
                f"--- GitHub Activity ({activity_window_label}) ---\n"
                f"{activity_text}"
            ),
        }],
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


def get_scrum_display_date(now=None, target_date=None):
    if target_date is not None:
        return target_date.strftime("%A, %d %b %Y")

    if now is None:
        now = datetime.now()

    if now.weekday() == 0:
        now = now - timedelta(days=3)

    return now.strftime("%A, %d %b %Y")


def ask_yes_no(prompt):
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")


# -----------------------------------------------
# SLACK
# -----------------------------------------------

def post_to_slack(summary, config, channel=None, schedule=None, cc=None, display_date=None):
    """Send a summary to Slack using chat.postMessage."""
    auth_token = config.get("slack_user_token") or config.get("slack_token")
    if not auth_token:
        raise ValueError("Missing Slack token in config (set SLACK_USER_TOKEN or SLACK_BOT_TOKEN)")

    target_channel = channel or config.get("slack_channel") or "#your-channel-name"

    today = get_scrum_display_date(target_date=display_date)
    schedule_value = schedule if schedule is not None else config.get("schedule", "")
    cc_value = cc if cc is not None else config.get("cc", "")
    schedule_line = f"4. Tentative schedule    {schedule_value}"
    cc_line = f"cc: {cc_value}"
    full_text = f"{summary}\n\n{schedule_line}\n{cc_line}"

    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        json={
            "channel": target_channel,
            "text": f"[{today}]\n{full_text}",
        },
        timeout=15,
    )

    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error: {data.get('error', 'unknown')}")

    return data


# -----------------------------------------------
# CLI
# -----------------------------------------------
def parse_args():
    def parse_cli_date(value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                "invalid date format; use YYYY-MM-DD"
            ) from exc

    parser = argparse.ArgumentParser(
        description="Generate a daily scrum briefing from your GitHub activity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  slack_committer                  fully AI-generated scrum\n"
            "  slack_committer --eta            prompt for arrival/schedule time\n"
            "  slack_committer --focus          prompt for Today's Focus (AI does sections 1-2)\n"
            "  slack_committer --date 2026-04-15  fetch activity for a specific date\n"
            "  slack_committer --eta --focus    prompt for both\n"
        ),
    )
    parser.add_argument(
        "--eta", action="store_true",
        help="prompt for your estimated arrival / schedule time",
    )
    parser.add_argument(
        "--focus", action="store_true",
        help="prompt for Today's Focus & Next Steps instead of AI-generating it",
    )
    parser.add_argument(
        "--date",
        type=parse_cli_date,
        metavar="YYYY-MM-DD",
        help="fetch GitHub activity for a specific UTC date",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config()

    env_var_names = {
        "github_token": "GITHUB_TOKEN",
        "github_username": "GITHUB_USERNAME",
        "groq_key": "GROQ_API_KEY",
    }
    missing = [env_var_names[k] for k in env_var_names if not config[k]]
    if missing:
        sys.exit(f"Error: missing required env vars: {', '.join(missing)}\n"
                 f"Set them in .env or export them before running.")

    print("Collecting GitHub activity...")
    activity, activity_window = collect_activity(config, target_date=args.date)
    print(f"  Found {len(activity)} item(s).\n")
    activity_text = format_activity(activity, window_label=activity_window)

    prompt = PROMPT_NO_FOCUS if args.focus else PROMPT_FULL

    print("Summarising with Groq...")
    summary = summarise(activity_text, prompt, config, activity_window_label=activity_window)

    if args.focus:
        print()
        focus = input("Today's Focus & Next Steps: ").strip()
        summary = f"{summary}\n\n3. Today's Focus & Next Steps:\n{focus}"

    schedule = config["schedule"]
    if args.eta:
        shift_hours = 5
        slots = [
            datetime(2000, 1, 1, 12, 0) + timedelta(minutes=30 * i)
            for i in range(13)  # 12:00 to 6:00 PM inclusive
        ]
        print()
        for i, start in enumerate(slots, 1):
            end = start + timedelta(hours=shift_hours)
            print(f"  {i:>2}.  {start.strftime('%-I:%M %p')} - {end.strftime('%-I:%M %p')}")
        print()
        while True:
            choice = input(f"Pick arrival time [1-{len(slots)}]: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(slots):
                start = slots[int(choice) - 1]
                end = start + timedelta(hours=shift_hours)
                schedule = f"{start.strftime('%-I:%M %p')} - {end.strftime('%-I:%M %p')}"
                break
            print(f"  Enter a number between 1 and {len(slots)}.")

    today = get_scrum_display_date(target_date=args.date)
    print(f"\n{'='*50}")
    print(f"Daily Scrum -- {today}")
    print('='*50)
    print(summary)
    print(f"\n4. Tentative schedule    {schedule}")
    print(f"cc: {config['cc']}")
    print('='*50)

    if config.get("slack_user_token") or config.get("slack_token"):
        if ask_yes_no("\nPost this scrum to Slack? (y/n): "):
            try:
                post_to_slack(
                    summary,
                    config,
                    schedule=schedule,
                    cc=config["cc"],
                    display_date=args.date,
                )
                print(f"Posted to Slack channel: {config.get('slack_channel')}")
            except (requests.RequestException, RuntimeError, ValueError) as e:
                print(f"Warning: could not post to Slack: {e}")
        else:
            print("Skipped Slack posting.")


if __name__ == "__main__":
    main()
