#!/usr/bin/env python3
"""
Hacker News poster for Wilderkin League marketing.

Submits stories to HN with tech/indie game angles.
No internal rate limiting — project-manager controls when this script runs.
Each invocation submits one story.

Usage:
  python3 hn_poster.py submit     # Submit the next story
  python3 hn_poster.py status     # Show posting stats

Requires HN_USERNAME, HN_PASSWORD in env.
"""

import json
import os
import sys
import re
import time
import random
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "wilderkin_hn_state.json"
GAME_URL = "https://wilderkinleague.com"
HN_BASE = "https://news.ycombinator.com"

# Story submissions with different HN-appropriate angles
STORY_QUEUE = [
    {
        "id": "show-hn-autobattler",
        "title": "Show HN: Free browser auto-battler with 95+ synergistic abilities",
        "url": GAME_URL,
        "type": "show",
    },
    {
        "id": "browser-game-tech",
        "title": "Wilderkin League - A pixel art auto-battler that runs entirely in the browser",
        "url": GAME_URL,
        "type": "show",
    },
    {
        "id": "ask-hn-browser-games",
        "title": "Ask HN: What browser games have impressed you with their depth?",
        "url": None,
        "text": (
            "I've been playing more browser games lately and I'm impressed by how far "
            "web tech has come for gaming. Games like Wilderkin League "
            f"({GAME_URL}) offer real strategy depth with zero download/install.\n\n"
            "What browser games have you found that punch above their weight in terms "
            "of gameplay depth? Interested in both technical and design aspects."
        ),
        "type": "ask",
    },
    {
        "id": "zero-friction-gaming",
        "title": "The case for zero-friction games: no download, no account, just play",
        "url": GAME_URL,
        "type": "show",
    },
]


def load_env():
    """Load HN credentials from env files or environment."""
    env = {}
    env_paths = [
        os.path.expanduser("~/.config/unstable-entity/social.env"),
        os.path.expanduser("~/.config/unstable-entity/hn.env"),
    ]
    for path in env_paths:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        env[key.strip()] = val.strip().strip('"').strip("'")

    for key in ["HN_USERNAME", "HN_PASSWORD"]:
        if key not in env and key in os.environ:
            env[key] = os.environ[key]
    return env


def load_state():
    """Load posting state."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "total_posts": 0,
        "queue_index": 0,
    }


def save_state(state):
    """Save posting state."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def make_opener():
    """Create urllib opener with cookie support."""
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)), cj


def hn_request(opener, path, data=None):
    """Make a request to HN."""
    url = f"{HN_BASE}/{path}"
    if data:
        data = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0")
    req.add_header("Referer", HN_BASE)
    try:
        resp = opener.open(req, timeout=15)
        return resp.read().decode("utf-8", errors="replace"), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return body, e.code


def hn_login(opener, username, password):
    """Login to HN. Returns True on success."""
    html, status = hn_request(opener, "login")
    fnid_match = re.search(r'name="fnid"\s+value="([^"]+)"', html)

    login_data = {"acct": username, "pw": password}
    if fnid_match:
        login_data["fnid"] = fnid_match.group(1)

    time.sleep(random.uniform(0.5, 1.5))
    html, status = hn_request(opener, "login", data=login_data)

    if "Bad login" in html:
        print(f"Login failed for {username}")
        return False

    print(f"Logged in as {username}")
    return True


def cmd_submit():
    """Submit the next story to HN."""
    env = load_env()

    username = env.get("HN_USERNAME")
    password = env.get("HN_PASSWORD")
    if not username or not password:
        print("ERROR: HN_USERNAME and HN_PASSWORD required")
        sys.exit(1)

    state = load_state()

    # Pick next story in rotation
    idx = state.get("queue_index", 0) % len(STORY_QUEUE)
    next_story = STORY_QUEUE[idx]

    # Login
    opener, cookies = make_opener()
    if not hn_login(opener, username, password):
        sys.exit(1)

    # Load submit page
    html, status = hn_request(opener, "submit")
    if status != 200:
        print(f"Failed to load submit page: HTTP {status}")
        sys.exit(1)

    fnid_match = re.search(r'name="fnid"\s+value="([^"]+)"', html)
    if not fnid_match:
        print("Could not find submit form. Account may need more karma first.")
        sys.exit(1)

    # Build submission
    submit_data = {
        "fnid": fnid_match.group(1),
        "fnop": "submit-page",
        "title": next_story["title"],
    }

    if next_story.get("url"):
        submit_data["url"] = next_story["url"]
    elif next_story.get("text"):
        submit_data["text"] = next_story["text"]

    time.sleep(random.uniform(2, 5))
    result_html, result_status = hn_request(opener, "r", data=submit_data)

    if result_status in (200, 301, 302):
        state["total_posts"] = state.get("total_posts", 0) + 1
        state["queue_index"] = (idx + 1) % len(STORY_QUEUE)
        save_state(state)

        print(f"Submitted: {next_story['title']}")
        print(f"Type: {next_story['type']}")
        print(f"Total HN posts: {state['total_posts']}")
    else:
        print(f"Submit may have failed. Status: {result_status}")
        sys.exit(1)


def cmd_status():
    """Show HN posting stats."""
    state = load_state()
    idx = state.get("queue_index", 0) % len(STORY_QUEUE)

    print(f"=== Wilderkin League HN Status ===")
    print(f"Total posts: {state.get('total_posts', 0)}")
    print(f"Next in queue: {STORY_QUEUE[idx]['title']}")
    print(f"Queue size: {len(STORY_QUEUE)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: hn_poster.py [submit|status]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "submit":
        cmd_submit()
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
