#!/usr/bin/env python3
"""
Mastodon/Fediverse poster for Wilderkin League marketing.

Posts gaming content to multiple Mastodon instances.
Each invocation posts one item from the queue, alternating instances.

Usage:
  python3 mastodon_poster.py post      # Post next item from queue
  python3 mastodon_poster.py status    # Show account status

Reads credentials from ~/.config/unstable-entity/mastodon.env and social.env.
"""

import json
import os
import sys
import random
import datetime
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "wilderkin_mastodon_state.json"
GAME_URL = "https://wilderkinleague.com"

# Mastodon instances with their credential env var names
INSTANCES = [
    {
        "name": "mstdn.ca",
        "url": "https://mstdn.ca",
        "token_key": "MSTDN_CA_ACCESS_TOKEN",
        "alt_token_key": None,
    },
    {
        "name": "mstdn.social",
        "url": "https://mstdn.social",
        "token_key": "MASTODON_ACCESS_TOKEN",
        "alt_token_key": "MSTDN_SOCIAL_ACCESS_TOKEN",
    },
    {
        "name": "toot.community",
        "url": "https://toot.community",
        "token_key": "TOOT_COMMUNITY_ACCESS_TOKEN",
        "alt_token_key": None,
    },
]

POST_QUEUE = [
    {
        "id": "autobattler-love",
        "text": (
            "Auto-battlers are the perfect genre for people who love strategy "
            "but hate mechanical skill requirements. Just brain, no reflexes.\n\n"
            "Been hooked on Wilderkin League lately - free browser auto-battler "
            "with 10 animal species and 95+ abilities. The synergy combos are "
            "surprisingly deep.\n\n" + GAME_URL + "\n\n"
            "#indiegame #autobattler #browsergame #gaming #strategy"
        ),
        "has_promo": True,
    },
    {
        "id": "pixel-art-games",
        "text": (
            "Hot take: pixel art ages better than any other art style in games. "
            "Super Nintendo games from 1993 still look gorgeous.\n\n"
            "Modern pixel art games that nail the aesthetic: Celeste, Stardew Valley, "
            "Dead Cells. Each proves you don't need AAA budgets for beautiful games.\n\n"
            "#pixelart #indiegame #gaming #gamedesign"
        ),
        "has_promo": False,
    },
    {
        "id": "browser-gaming-comeback",
        "text": (
            "Browser games are quietly making a comeback and I'm here for it. "
            "No launcher, no 50GB download, no account creation. Just click and play.\n\n"
            "Currently enjoying Wilderkin League - a pixel art auto-battler "
            "with creature synergies. Zero friction to try: " + GAME_URL + "\n\n"
            "#browsergame #indiegaming #webgames #gaming"
        ),
        "has_promo": True,
    },
    {
        "id": "strategy-depth",
        "text": (
            "The best strategy games are easy to learn, impossible to master. "
            "Chess, Go, Slay the Spire - simple rules, endless depth.\n\n"
            "Auto-battlers hit this sweet spot perfectly. Each match is a new puzzle "
            "with the same building blocks.\n\n"
            "#strategy #gaming #autobattler #indiegame #gamedesign"
        ),
        "has_promo": False,
    },
    {
        "id": "lunch-break-pick",
        "text": (
            "My lunch break gaming rotation right now:\n\n"
            "- Wilderkin League (browser auto-battler, ~15 min matches)\n"
            "- NYT crossword\n"
            "- Whatever roguelike I'm currently failing at\n\n"
            "Wilderkin is free, no install: " + GAME_URL + "\n\n"
            "What's in your lunch break rotation?\n\n"
            "#gaming #browsergame #indiegaming #autobattler"
        ),
        "has_promo": True,
    },
    {
        "id": "creature-design",
        "text": (
            "Creature design in games is an underappreciated art form. "
            "Each creature needs to visually communicate its role, abilities, "
            "and personality in a few pixels.\n\n"
            "Pokemon nailed this. Monster Hunter nailed this. Even small indie "
            "games can get it right with thoughtful design.\n\n"
            "#gamedesign #pixelart #indiegame #creature #art"
        ),
        "has_promo": False,
    },
    {
        "id": "synergy-discovery",
        "text": (
            "That moment in an auto-battler when you accidentally discover "
            "a broken synergy combo and everything clicks...\n\n"
            "Had this in Wilderkin League today - stacked two species with "
            "complementary abilities and suddenly my team was unkillable. "
            "95+ abilities means there's always something new to find.\n\n" + GAME_URL + "\n\n"
            "#autobattler #indiegame #gaming #browsergame #strategy"
        ),
        "has_promo": True,
    },
    {
        "id": "indie-game-support",
        "text": (
            "Supporting indie game devs is important. These people pour years "
            "of their lives into passion projects that compete with billion-dollar studios.\n\n"
            "Best way to support: play their games, leave reviews, tell a friend. "
            "It costs nothing but means everything.\n\n"
            "#indiegame #indiegaming #gamedev #supportindies"
        ),
        "has_promo": False,
    },
    {
        "id": "free-games-quality",
        "text": (
            "The quality of free indie games in 2026 is insane. No ads, no microtransactions, "
            "just devs who wanted to make something cool.\n\n"
            "Latest example: Wilderkin League. Browser auto-battler, 10 species, "
            "95+ abilities, pixel art. Completely free, no account needed.\n\n"
            "Try it: " + GAME_URL + "\n\n"
            "#indiegame #freegames #browsergame #autobattler #pixelart"
        ),
        "has_promo": True,
    },
    {
        "id": "turn-based-appreciation",
        "text": (
            "Unpopular opinion: turn-based games respect your time more than "
            "real-time games. You can think, strategize, even walk away mid-turn.\n\n"
            "No panic clicks, no ping-dependent outcomes. Just pure decision-making.\n\n"
            "#gaming #turnbased #strategy #autobattler #indiegame"
        ),
        "has_promo": False,
    },
    {
        "id": "animal-themed-games",
        "text": (
            "Games with animal characters just hit different. Pokemon, Super Auto Pets, "
            "Okami, Night in the Woods...\n\n"
            "Been playing Wilderkin League - auto-battler with 10 animal species, "
            "each with unique abilities and pixel art design. "
            "Free in the browser: " + GAME_URL + "\n\n"
            "What's your favorite animal-themed game?\n\n"
            "#gaming #indiegame #autobattler #pixelart #browsergame"
        ),
        "has_promo": True,
    },
    {
        "id": "no-download-revolution",
        "text": (
            "We went from 'insert cartridge' to 'download 100GB' and now back to "
            "'just open a URL.' Full circle.\n\n"
            "Browser games aren't just Flash nostalgia anymore. Modern web tech "
            "enables real games with real depth. The future is URL-first.\n\n"
            "#webdev #browsergame #gaming #indiegaming #gamedev"
        ),
        "has_promo": False,
    },
]


def load_env():
    """Load credentials from env files and environment."""
    env = {}
    env_paths = [
        os.path.expanduser("~/.config/unstable-entity/mastodon.env"),
        os.path.expanduser("~/.config/unstable-entity/social.env"),
    ]
    for path in env_paths:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        env[key.strip()] = val.strip().strip('"').strip("'")
    # Load mstdn.ca credentials separately to avoid key collisions
    mstdn_ca_path = os.path.expanduser("~/.config/unstable-entity/mstdn_ca.env")
    if os.path.exists(mstdn_ca_path):
        with open(mstdn_ca_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    # Prefix mstdn.ca keys to avoid collision with other instances
                    if key == "MASTODON_ACCESS_TOKEN":
                        env["MSTDN_CA_ACCESS_TOKEN"] = val
                    elif key == "MASTODON_INSTANCE":
                        env["MSTDN_CA_INSTANCE"] = val
                    else:
                        env[key] = val
    for key in ["MASTODON_ACCESS_TOKEN", "MASTODON_INSTANCE",
                "MSTDN_SOCIAL_ACCESS_TOKEN", "TOOT_COMMUNITY_ACCESS_TOKEN",
                "MSTDN_CA_ACCESS_TOKEN"]:
        if key not in env and key in os.environ:
            env[key] = os.environ[key]
    return env


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"queue_index": 0, "total_posts": 0, "instance_index": 0}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def mastodon_api(instance_url, endpoint, method="GET", data=None, token=None):
    """Make a Mastodon API request."""
    url = f"{instance_url}/api/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "WilderkinBot/1.0",
    }
    if data:
        encoded = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=encoded, headers=headers, method=method)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    else:
        req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"Mastodon API error {e.code}: {body[:200]}")
        return None
    except Exception as e:
        print(f"Request error: {e}")
        return None


def get_available_instances(env):
    """Return list of instances with valid tokens."""
    available = []
    for inst in INSTANCES:
        token = env.get(inst["token_key"])
        if not token and inst.get("alt_token_key"):
            token = env.get(inst["alt_token_key"])
        if token:
            available.append({"name": inst["name"], "url": inst["url"], "token": token})
    return available


def cmd_post():
    """Post next item from queue, alternating between instances."""
    env = load_env()
    available = get_available_instances(env)

    if not available:
        print("ERROR: No Mastodon access tokens found")
        sys.exit(1)

    state = load_state()

    # Pick next post
    idx = state.get("queue_index", 0) % len(POST_QUEUE)
    next_post = POST_QUEUE[idx]

    # Pick instance (alternate)
    inst_idx = state.get("instance_index", 0) % len(available)
    instance = available[inst_idx]

    print(f"Posting to {instance['name']}...")

    result = mastodon_api(
        instance["url"],
        "statuses",
        method="POST",
        data={"status": next_post["text"], "visibility": "public"},
        token=instance["token"],
    )

    # Try all instances starting from inst_idx
    posted = False
    for attempt in range(len(available)):
        try_idx = (inst_idx + attempt) % len(available)
        try_instance = available[try_idx]
        if attempt > 0:
            print(f"Trying fallback: {try_instance['name']}...")
        result = mastodon_api(
            try_instance["url"],
            "statuses",
            method="POST",
            data={"status": next_post["text"], "visibility": "public"},
            token=try_instance["token"],
        )
        if result and "id" in result:
            state["queue_index"] = (idx + 1) % len(POST_QUEUE)
            state["instance_index"] = (try_idx + 1) % len(available)
            state["total_posts"] = state.get("total_posts", 0) + 1
            save_state(state)
            post_url = result.get("url", f"{try_instance['url']}/statuses/{result['id']}")
            print(f"Posted: {next_post['id']}")
            print(f"Instance: {try_instance['name']}")
            print(f"URL: {post_url}")
            print(f"Promo: {'yes' if next_post['has_promo'] else 'no'}")
            print(f"Total posts: {state['total_posts']}")
            posted = True
            break
        else:
            print(f"Failed on {try_instance['name']}: {result}")

    if not posted:
        print("All instances failed")
        sys.exit(1)


def cmd_status():
    state = load_state()
    env = load_env()
    available = get_available_instances(env)
    idx = state.get("queue_index", 0) % len(POST_QUEUE)

    print(f"=== Wilderkin League Mastodon Status ===")
    print(f"Total posts: {state.get('total_posts', 0)}")
    print(f"Next in queue: {POST_QUEUE[idx]['id']}")
    print(f"Queue size: {len(POST_QUEUE)}")
    print(f"Available instances: {len(available)}")
    for inst in available:
        print(f"  - {inst['name']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: mastodon_poster.py [post|status]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "post":
        cmd_post()
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
