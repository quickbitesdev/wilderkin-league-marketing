#!/usr/bin/env python3
"""
Bluesky poster for Wilderkin League marketing.

Posts gaming content to Bluesky with gaming hashtags, mixing genuine
gaming discussion with Wilderkin League mentions (~50/50).

No internal rate limiting — project-manager controls when this script runs.
Each invocation posts one message.

Usage:
  python3 bluesky_poster.py post      # Post to Bluesky
  python3 bluesky_poster.py status    # Show posting stats

Credentials: BLUESKY_HANDLE, BLUESKY_PASSWORD from env.
"""

import json
import os
import sys
import random
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "wilderkin_bluesky_state.json"

GAME_URL = "https://wilderkinleague.com"

# Post templates — mix of genuine gaming content and Wilderkin mentions
GENERIC_GAMING_POSTS = [
    "auto-battlers are genuinely the most underrated genre right now. the strategy depth in some of these indie ones is wild #gamedev #indiegames #autobattler",
    "pixel art games just hit different. there's something about the aesthetic that makes you actually focus on gameplay #pixelart #indiegames #gaming",
    "been on a browser games kick lately. no download, no install, just click and play. why aren't more devs doing this? #webdev #gamedev #browsergames",
    "synergy-based combat systems are so satisfying when they click. finding that perfect combo is peak gaming #strategy #autobattler #gaming",
    "indie game devs making browser games are doing god's work. zero friction to try something new #indiegames #gamedev #webgames",
]

WILDERKIN_POSTS = [
    "been playing Wilderkin League — free browser auto-battler with 10 animal species. the synergy system is surprisingly deep for a browser game {url} #autobattler #indiegames #gaming",
    "if you're into auto-battlers, Wilderkin League is worth a look. 95+ abilities, runs in browser, no download. pixel art style too {url} #gamedev #pixelart #autobattler",
    "found this neat browser auto-battler called Wilderkin League. each species plays totally different — the synergy combos get wild {url} #indiegames #browsergames #strategy",
    "Wilderkin League tier list debate: are foxes or wolves better? the burst vs sustain tradeoff is real in this game {url} #autobattler #gaming #strategy",
    "no-download browser auto-battler with pixel art animals fighting each other? yes please. Wilderkin League scratches that itch {url} #indiegames #pixelart #autobattler",
]


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"total_posted": 0, "last_text": ""}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def pick_post(state):
    """Pick a post template, alternating between generic and wilderkin. Avoid repeating last post."""
    last_text = state.get("last_text", "")

    # 50/50 split
    if random.random() < 0.5:
        pool = GENERIC_GAMING_POSTS
    else:
        pool = WILDERKIN_POSTS

    candidates = [t.format(url=GAME_URL) for t in pool]

    # Avoid repeating last post
    if last_text and len(candidates) > 1:
        candidates = [t for t in candidates if t != last_text]

    return random.choice(candidates)


def post_to_bluesky(text):
    """Post to Bluesky using atproto."""
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_PASSWORD")

    if not handle or not password:
        print("Missing BLUESKY_HANDLE or BLUESKY_PASSWORD")
        return False

    try:
        from atproto import Client
    except ImportError:
        print("atproto not installed. Install with: pip install atproto")
        return False

    try:
        client = Client()
        client.login(handle, password)
        client.send_post(text=text)
        print(f"Posted to Bluesky: {text[:80]}...")
        return True
    except Exception as e:
        print(f"Bluesky post failed: {e}")
        return False


def cmd_post():
    state = load_state()
    text = pick_post(state)
    success = post_to_bluesky(text)

    if success:
        state["total_posted"] = state.get("total_posted", 0) + 1
        state["last_text"] = text
        save_state(state)
        print(f"Successfully posted to Bluesky (total: {state['total_posted']})")
        return 0
    else:
        return 1


def cmd_status():
    state = load_state()
    print(f"Total posted: {state.get('total_posted', 0)}")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "post":
        sys.exit(cmd_post())
    elif cmd == "status":
        sys.exit(cmd_status())
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
