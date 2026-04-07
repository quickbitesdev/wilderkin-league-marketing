#!/usr/bin/env python3
"""
Dev.to article poster for Wilderkin League marketing.

Publishes developer-perspective articles about building a browser auto-battler.
No internal rate limiting — project-manager controls when this script runs.
Each invocation publishes one article.

Usage:
  python3 devto_poster.py post      # Publish an article
  python3 devto_poster.py status    # Show publishing stats

Credentials: DEVTO_API_KEY from env.
"""

import json
import os
import sys
import requests
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "wilderkin_devto_state.json"

GAME_URL = "https://wilderkinleague.com"
DEVTO_API = "https://dev.to/api/articles"

# Full article templates (~300 words each), developer perspective
ARTICLES = [
    {
        "title": "I built a free browser auto-battler with 95+ abilities",
        "tags": ["webdev", "gamedev", "javascript", "opensource"],
        "body": """
I've been working on a browser-based auto-battler called Wilderkin League, and I wanted to share some lessons from the journey.

## The concept

Auto-battlers are strategy games where you pick units and they fight automatically. Think Teamfight Tactics or Super Auto Pets, but entirely in the browser — no download needed.

Wilderkin League features 10 animal species, each with unique abilities, and over 95 total abilities that create complex synergy combinations.

## Why browser-only?

I wanted zero friction. No app store, no Steam page, no installer. Just a URL you can share and anyone can play immediately. This turned out to be one of the best decisions — the conversion rate from "seeing a link" to "actually playing" is way higher than any downloadable game I've made.

## Technical stack

The game runs on vanilla JavaScript with HTML5 Canvas for rendering. The pixel art is hand-crafted and the entire game loads in under 2 seconds on most connections.

The synergy system was the hardest part to balance. With 10 species and 95+ abilities, the number of possible combinations is enormous. I built a simulation framework that plays thousands of matches to identify overpowered combos.

## What I learned

1. **Browser games are underrated** — the reach is incredible
2. **Pixel art saves time** — and players love the aesthetic
3. **Auto-battlers are perfect for casual sessions** — games take 3-5 minutes
4. **Synergy depth keeps players coming back** — finding new combos is addictive

If you want to try it out, it's completely free at [wilderkinleague.com]({url}).

Would love to hear feedback from other gamedevs here!
""".strip(),
    },
    {
        "title": "How synergy systems work in auto-battlers — a developer deep dive",
        "tags": ["gamedev", "javascript", "webdev", "tutorial"],
        "body": """
Synergy systems are the backbone of auto-battler games. I've spent months building one for my browser game Wilderkin League, and here's what I've learned about making them feel satisfying.

## What makes a good synergy system?

A synergy system needs to reward players for combining specific units while keeping the game balanced. The key tension is: strong combos should feel powerful, but not unbeatable.

## The design approach

In Wilderkin League, each of the 10 animal species has a "species bonus" that activates when you have multiple units of that type. For example:

- **Wolves**: Pack bonus — each wolf buffs adjacent wolves
- **Foxes**: Trickster bonus — chance to dodge and counter-attack
- **Bears**: Endurance bonus — increased HP and regeneration

But the real depth comes from cross-species synergies. A wolf-bear combo creates a tanky frontline, while fox-bird creates a high-mobility glass cannon team.

## Balancing 95+ abilities

With this many abilities, manual balancing is impossible. I built an automated tournament system that runs thousands of matches between random team compositions. If any combo wins more than 60% of its matches, it gets flagged for adjustment.

## The meta evolves

Players find combos I never anticipated. That's actually the best part — watching the meta develop organically. Each balance patch shifts the landscape and players discover new strategies.

## Key takeaways for gamedevs

1. **Start simple, add complexity gradually** — my first version had 5 species
2. **Automated balancing saves your sanity** — you can't playtest every combo
3. **Cross-type synergies create the deepest strategy** — not just same-type bonuses
4. **Let players surprise you** — they'll find things you never designed

Try the game free at [wilderkinleague.com]({url}) — I'd love to hear what combos you discover.
""".strip(),
    },
    {
        "title": "Lessons from making a pixel art browser game in 2026",
        "tags": ["gamedev", "pixelart", "webdev", "javascript"],
        "body": """
I recently launched a pixel art browser game called Wilderkin League — a free auto-battler featuring animal species. Here are some hard-won lessons from the process.

## Pixel art is not "easy mode"

A lot of devs think pixel art is the shortcut to shipping a game. It's not. Good pixel art requires understanding of color theory, animation principles, and readability at small sizes. But it does have one huge advantage: iteration speed. Changing a pixel art sprite takes minutes, not hours.

## Browser deployment changes everything

When your game runs in a browser, your distribution strategy completely changes:

- **No app store reviews** — ship when you want
- **Instant sharing** — just send a URL
- **No install friction** — players try your game in seconds
- **Cross-platform by default** — works on phone, tablet, desktop

The downside? You're competing with the entire internet for attention. Discovery is the real challenge.

## What worked for marketing

As a solo dev, I focused on:

1. **Reddit communities** — genuine participation in r/autobattler, r/pixelart, r/indiegaming
2. **Dev blogs** — sharing the technical journey (like this post)
3. **Direct links** — the zero-friction URL is your best asset

## Performance matters more than you think

Browser games need to load fast. I obsessed over keeping the initial load under 2 seconds. Every sprite sheet is optimized, JavaScript is minified, and assets load progressively. Players will bounce if your game doesn't start immediately.

## The result

Wilderkin League now has 10 species, 95+ abilities, and runs entirely in the browser. No download, no sign-up, completely free.

Play it at [wilderkinleague.com]({url}) — feedback always welcome!
""".strip(),
    },
]


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"queue_index": 0, "total_published": 0}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def pick_article(state):
    """Pick the next article in rotation."""
    idx = state.get("queue_index", 0) % len(ARTICLES)
    return ARTICLES[idx], idx


def publish_article(article):
    """Publish to Dev.to via API."""
    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key:
        print("Missing DEVTO_API_KEY")
        return False

    body = article["body"].format(url=GAME_URL)

    payload = {
        "article": {
            "title": article["title"],
            "body_markdown": body,
            "published": True,
            "tags": article["tags"],
        }
    }

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(DEVTO_API, json=payload, headers=headers, timeout=30)
        if resp.status_code in (200, 201):
            data = resp.json()
            print(f"Published: {data.get('url', 'unknown URL')}")
            return True
        else:
            print(f"Dev.to API error {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"Dev.to post failed: {e}")
        return False


def cmd_post():
    state = load_state()

    article, idx = pick_article(state)
    success = publish_article(article)

    if success:
        state["queue_index"] = (idx + 1) % len(ARTICLES)
        state["total_published"] = state.get("total_published", 0) + 1
        save_state(state)
        print(f"Successfully published to Dev.to (total: {state['total_published']})")
        return 0
    else:
        return 1


def cmd_status():
    state = load_state()
    idx = state.get("queue_index", 0) % len(ARTICLES)
    print(f"Total published: {state.get('total_published', 0)}")
    print(f"Next article: {ARTICLES[idx]['title']}")
    print(f"Queue size: {len(ARTICLES)}")
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
