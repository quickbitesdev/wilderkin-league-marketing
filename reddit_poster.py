#!/usr/bin/env python3
"""
Reddit poster for Wilderkin League marketing.

Posts authentic gaming content to relevant subreddits, naturally mentioning
Wilderkin League as a genuine player discovery.

No internal rate limiting — project-manager controls when this script runs.
Each invocation picks one subreddit and posts one message.

Usage:
  python3 reddit_poster.py post      # Post to one subreddit
  python3 reddit_poster.py status    # Show posting stats

Credentials: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD
from social.env or environment variables.
"""

import json
import os
import sys
import random
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "wilderkin_reddit_state.json"
PERSONA_FILE = SCRIPT_DIR / "personas" / "player1.json"

GAME_URL = "https://wilderkinleague.com"

# Target subreddits — rotated through one at a time
SUBREDDITS = [
    "indiegaming",
    "indiegames",
    "WebGames",
    "autobattler",
    "pixelart",
    "gamedev",
    "AndroidGaming",
    "pcgaming",
]

# Post templates — each is a natural-sounding post from a real player's perspective.
POST_TEMPLATES = [
    {
        "id": "discovery-autobattler",
        "subreddits": ["autobattler", "indiegaming"],
        "title": "Found a browser auto-battler with a surprisingly deep synergy system",
        "body": (
            "Been on an auto-battler kick lately (TFT, Super Auto Pets, etc) and stumbled "
            "on Wilderkin League. It's free, runs in the browser, no download or account needed.\n\n"
            "What surprised me is the depth — 10 animal species with 95+ abilities, and the "
            "synergy combos between species actually matter. Had a match where stacking "
            "two flyers with a ground tank completely changed the outcome.\n\n"
            "Anyone else tried it? Curious what comps people are running.\n\n"
            f"{GAME_URL}"
        ),
    },
    {
        "id": "lunch-break-games",
        "subreddits": ["WebGames", "indiegaming", "pcgaming"],
        "title": "Best browser games you can play during a lunch break?",
        "body": (
            "Looking for games I can jump into quickly without installing anything. "
            "Ideally something with some strategy depth but that works in 15-20 min sessions.\n\n"
            "I've been playing Wilderkin League lately — it's a pixel art auto-battler "
            "that runs entirely in the browser. Quick matches but surprisingly tactical "
            f"with the ability synergies. {GAME_URL}\n\n"
            "What are your go-to browser games for short sessions?"
        ),
    },
    {
        "id": "pixel-art-appreciation",
        "subreddits": ["pixelart", "indiegames"],
        "title": "Loving the pixel art style in recent indie auto-battlers",
        "body": (
            "There's something about well-done pixel art in strategy games that just hits "
            "different. The animations feel more intentional and readable than 3D.\n\n"
            "Been playing Wilderkin League which has this really clean pixel art with "
            "10 different animal species, each with distinct visual design. The attack "
            "animations are simple but satisfying.\n\n"
            "What are some other pixel art games with great creature/character design?"
        ),
    },
    {
        "id": "no-install-gaming",
        "subreddits": ["WebGames", "AndroidGaming", "pcgaming"],
        "title": "Underrated advantage of browser games: zero friction to try",
        "body": (
            "I've started appreciating browser games more lately. No download, no account "
            "creation, no launcher updates. Just click and play.\n\n"
            "Found Wilderkin League this way — someone linked it, I clicked, was playing "
            "in 5 seconds. It's an auto-battler with animal species and ability synergies. "
            f"Free, no sign-up needed: {GAME_URL}\n\n"
            "Are browser-based games making a comeback or is it just me noticing them more?"
        ),
    },
    {
        "id": "synergy-systems",
        "subreddits": ["autobattler", "indiegames", "gamedev"],
        "title": "What makes a good synergy system in auto-battlers?",
        "body": (
            "I've been thinking about what separates a great synergy system from a mediocre one. "
            "TFT has trait bonuses, SAP has food buffs + animal triggers.\n\n"
            "Recently started playing Wilderkin League which does it differently — "
            "10 animal species with 95+ abilities, and the synergies come from how abilities "
            "interact rather than just stacking same-type units.\n\n"
            "What games do you think have the best-designed synergy mechanics? "
            "And for devs: how do you balance emergent combos without killing creativity?"
        ),
    },
    {
        "id": "indie-gems-thread",
        "subreddits": ["indiegaming", "indiegames"],
        "title": "What indie game did you recently discover that deserves more attention?",
        "body": (
            "Always looking for under-the-radar indie games. I'll start:\n\n"
            "Wilderkin League — a free browser auto-battler with pixel art. "
            "10 animal species, each with unique abilities. The synergy system between "
            "species creates interesting strategic decisions. No download, no account "
            f"needed. {GAME_URL}\n\n"
            "What's your recent indie discovery?"
        ),
    },
    {
        "id": "gamedev-browser-question",
        "subreddits": ["gamedev", "WebGames"],
        "title": "Are browser games viable in 2026? Interested in the tech behind them",
        "body": (
            "Played a few browser games recently that felt surprisingly polished — "
            "Wilderkin League being one (auto-battler with pixel art, 95+ abilities). "
            "Made me curious about the tech stack.\n\n"
            "For browser game devs: what frameworks/engines are you using? "
            "How do you handle things like state persistence and matchmaking "
            "without a heavy backend? Is WebGL/Canvas still the way to go for 2D?"
        ),
    },
    {
        "id": "autobattler-comparison",
        "subreddits": ["autobattler", "indiegaming"],
        "title": "Tier list of free auto-battlers you can play right now",
        "body": (
            "Made a personal tier list of free auto-battlers I've tried:\n\n"
            "**S tier:** TFT (if you have League installed)\n"
            "**A tier:** Super Auto Pets, Wilderkin League (browser, no install needed)\n"
            "**B tier:** Storybook Brawl (RIP but was great)\n\n"
            "Wilderkin League surprised me — 10 species, 95+ abilities, real synergy depth. "
            f"And it's completely free in the browser: {GAME_URL}\n\n"
            "What would your tier list look like? What am I missing?"
        ),
    },
    {
        "id": "mobile-browser-gaming",
        "subreddits": ["AndroidGaming", "WebGames"],
        "title": "Browser games that work well on mobile?",
        "body": (
            "Looking for games that run in mobile Chrome/Firefox without needing an app. "
            "Ideally strategy or puzzle games, not endless runners.\n\n"
            "Wilderkin League works pretty well on my phone — it's an auto-battler so "
            "the turn-based nature means no precision tapping needed. "
            f"Free, no app install: {GAME_URL}\n\n"
            "What other browser games play well on mobile?"
        ),
    },
    {
        "id": "creature-collector-fan",
        "subreddits": ["indiegaming", "indiegames", "pixelart"],
        "title": "Anyone else love games where you collect and combine creatures?",
        "body": (
            "Pokemon got me hooked on the creature collecting formula as a kid, "
            "and I still gravitate toward games with that loop.\n\n"
            "Latest find: Wilderkin League, a browser auto-battler with 10 animal species. "
            "It's not exactly creature collecting but the way you build teams from different "
            "species and discover ability synergies scratches that same itch.\n\n"
            "What are your favorite creature-based indie games?"
        ),
    },
]


def load_env():
    """Load Reddit credentials from social.env or environment."""
    env_paths = [
        os.path.expanduser("~/.config/unstable-entity/social.env"),
        os.path.expanduser("~/.config/unstable-entity/reddit.env"),
    ]
    env = {}
    for path in env_paths:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        env[key.strip()] = val.strip().strip('"').strip("'")

    for key in ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"]:
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
        "subreddit_index": 0,
        "last_template_per_subreddit": {},
    }


def save_state(state):
    """Save posting state."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_persona():
    """Load the player persona."""
    if PERSONA_FILE.exists():
        with open(PERSONA_FILE) as f:
            return json.load(f)
    return {"username": "pixelwarden_gaming"}


def pick_subreddit(state):
    """Pick the next subreddit in rotation."""
    idx = state.get("subreddit_index", 0) % len(SUBREDDITS)
    return SUBREDDITS[idx], idx


def pick_post(state, subreddit):
    """Pick a template for this subreddit, avoiding the last one used for it."""
    last_used = state.get("last_template_per_subreddit", {}).get(subreddit)

    # Find templates that target this subreddit
    candidates = [p for p in POST_TEMPLATES if subreddit in p["subreddits"]]
    if not candidates:
        # Fallback: use any template
        candidates = list(POST_TEMPLATES)

    # Avoid repeating the last template used for this subreddit
    if last_used and len(candidates) > 1:
        candidates = [p for p in candidates if p["id"] != last_used]

    return random.choice(candidates)


def get_modhash(session_cookie):
    """Get modhash for CSRF via session cookie."""
    import http.cookiejar
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request("https://www.reddit.com/api/me.json")
    req.add_header("Cookie", f"reddit_session={urllib.parse.quote(session_cookie)}")
    req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64)")
    req.add_header("Accept", "application/json")
    with opener.open(req, timeout=15) as r:
        data = json.loads(r.read())
        return data["data"]["modhash"], jar


def submit_post_via_session(session_cookie, subreddit, title, body):
    """Submit a self post using session cookie authentication."""
    modhash, jar = get_modhash(session_cookie)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    payload = urllib.parse.urlencode({
        "api_type": "json",
        "kind": "self",
        "sr": subreddit,
        "title": title,
        "text": body,
        "uh": modhash,
        "resubmit": "true",
    }).encode()
    req = urllib.request.Request("https://www.reddit.com/api/submit", data=payload)
    req.add_header("Cookie", f"reddit_session={urllib.parse.quote(session_cookie)}")
    req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64)")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("X-Modhash", modhash)
    with opener.open(req, timeout=20) as r:
        return json.loads(r.read())


def cmd_post():
    """Post to one subreddit."""
    env = load_env()

    # Try session-based posting first, fall back to praw if session not available
    session = env.get("REDDIT_SESSION") or env.get("REDDIT_SESSION_2")
    if not session:
        required = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"]
        missing = [k for k in required if k not in env]
        if missing:
            print(f"Missing credentials: {', '.join(missing)}")
            sys.exit(1)

    state = load_state()

    # Pick next subreddit in rotation
    subreddit, idx = pick_subreddit(state)

    # Pick a post template (avoid repeating last one for this subreddit)
    post = pick_post(state, subreddit)

    if session:
        try:
            result = submit_post_via_session(session, subreddit, post["title"], post["body"])
            errors = result.get("json", {}).get("errors", [])
            data = result.get("json", {}).get("data", {})
            if errors:
                print(f"Reddit errors: {errors}")
                # Try second session if available
                session2 = env.get("REDDIT_SESSION_2")
                if session2 and session != session2:
                    print("Trying second session...")
                    result = submit_post_via_session(session2, subreddit, post["title"], post["body"])
                    errors = result.get("json", {}).get("errors", [])
                    data = result.get("json", {}).get("data", {})
                if errors:
                    print(f"All sessions failed: {errors}")
                    sys.exit(1)
            permalink = data.get("url", "")
            state["total_posts"] = state.get("total_posts", 0) + 1
            state["subreddit_index"] = (idx + 1) % len(SUBREDDITS)
            if "last_template_per_subreddit" not in state:
                state["last_template_per_subreddit"] = {}
            state["last_template_per_subreddit"][subreddit] = post["id"]
            save_state(state)
            print(f"Posted successfully to r/{subreddit}")
            print(f"Title: {post['title']}")
            print(f"URL: {permalink}")
            print(f"Total posts: {state['total_posts']}")
        except Exception as e:
            print(f"Failed to post: {e}")
            sys.exit(1)
    else:
        try:
            import praw
        except ImportError:
            print("ERROR: praw not installed. Run: pip install praw")
            sys.exit(1)

        reddit = praw.Reddit(
            client_id=env["REDDIT_CLIENT_ID"],
            client_secret=env["REDDIT_CLIENT_SECRET"],
            username=env["REDDIT_USERNAME"],
            password=env["REDDIT_PASSWORD"],
            user_agent="WilderkinFan/1.0 (by u/{})".format(env["REDDIT_USERNAME"]),
        )
        try:
            sub = reddit.subreddit(subreddit)
            submission = sub.submit(title=post["title"], selftext=post["body"])
            state["total_posts"] = state.get("total_posts", 0) + 1
            state["subreddit_index"] = (idx + 1) % len(SUBREDDITS)
            if "last_template_per_subreddit" not in state:
                state["last_template_per_subreddit"] = {}
            state["last_template_per_subreddit"][subreddit] = post["id"]
            save_state(state)
            print(f"Posted successfully to r/{subreddit}")
            print(f"Title: {post['title']}")
            print(f"URL: https://reddit.com{submission.permalink}")
            print(f"Total posts: {state['total_posts']}")
        except Exception as e:
            print(f"Failed to post to r/{subreddit}: {e}")
            sys.exit(1)


def cmd_status():
    """Show posting statistics."""
    state = load_state()
    persona = load_persona()

    print(f"=== Wilderkin League Reddit Status ===")
    print(f"Persona: {persona.get('name', '?')} (@{persona.get('username', '?')})")
    print(f"Total posts: {state.get('total_posts', 0)}")

    idx = state.get("subreddit_index", 0) % len(SUBREDDITS)
    print(f"Next subreddit: r/{SUBREDDITS[idx]}")
    print(f"Templates available: {len(POST_TEMPLATES)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: reddit_poster.py [post|status]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "post":
        cmd_post()
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
