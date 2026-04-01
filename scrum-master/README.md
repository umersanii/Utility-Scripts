scrum_master — Daily GitHub Scrum Briefing
=========================================

Overview
--------
This small script collects your commits and pull requests from the last 24 hours
across configured repositories, summarises them via Groq, and prints a concise
daily scrum briefing to the terminal.

Requirements
------------
- Python 3.8+
- pip packages: `requests`, `groq`, `python-dotenv`

Install
-------
Run:

```
pip install requests groq python-dotenv
```

Setup
-----
1. Place a `.env` file in the same directory as the script (or export the
   environment variables). Required variables:

- `GITHUB_TOKEN` — personal access token (read access to repo/PRs)
- `GITHUB_USERNAME` — your GitHub login
- `GROQ_API_KEY` — API key for Groq
- `REPOS` — comma-separated list of repositories (e.g. `org/repo1,org/repo2`)
- `SCHEDULE` — optional default schedule string (e.g. `3:00 pm - 8:00 pm`)
- `CC` — optional CC text to show in output

Example `.env`:

```
GITHUB_TOKEN=ghp_...
GITHUB_USERNAME=youruser
GROQ_API_KEY=groq_...
REPOS=beetleOps/edgevision_mobile,beetleOps/EdgeVision_Core
SCHEDULE=3:00 pm - 8:00 pm
CC=@YourManager
```

Usage
-----
Make the script executable or run with Python:

```
./scrum_master
python3 scrum_master
```

Flags:

- `--eta`  : Prompts you to pick an arrival time slot (adjusts schedule)
- `--focus`: Prompts for "Today's Focus & Next Steps" instead of auto-generating it

Output
------
The script prints a 3-part (or 2-part) scrum summary, plus a tentative schedule
and CC line. If no activity is found it will print a short message.

Notes & Troubleshooting
-----------------------
- If required env vars are missing the script exits with an error listing them.
- Ensure `GITHUB_TOKEN` has permission to read the repos/PRs you query.
- The summarisation uses Groq — ensure your `GROQ_API_KEY` is valid and has
  quota for chat completions.

Files
-----
- [scrum_master](scrum_master) — main script

License
-------
Small internal helper — adapt as needed.
