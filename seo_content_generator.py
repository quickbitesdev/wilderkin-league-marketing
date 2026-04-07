#!/usr/bin/env python3
"""
SEO content generator for Wilderkin League.
Generates pre-written SEO content. No external API needed.
"""

import json, os, sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "wilderkin_seo_state.json"
OUTPUT_DIR = SCRIPT_DIR / "seo_output"
GAME_URL = "https://wilderkinleague.com"

SEO_PAGES = [
    {
        "slug": "tier-list",
        "filename": "wilderkin-league-tier-list.md",
        "content": (
            "# Wilderkin League Tier List - Best Species Ranked (2026)\n\n"
            "Looking for the best species in Wilderkin League? This tier list ranks all 10 animal species.\n\n"
            "## S Tier\n"
            "**Wolf** - Pack synergy is incredibly strong. Multiple wolves buff each other.\n"
            "**Fox** - Trickster abilities give Fox the highest outplay potential.\n\n"
            "## A Tier\n"
            "**Bear** - Incredible sustain with HP regeneration and high base stats.\n"
            "**Eagle** - High mobility and burst damage. Aerial abilities bypass frontline.\n"
            "**Snake** - Poison synergies deal stacking damage over time.\n\n"
            "## B Tier\n"
            "**Owl** - Wisdom abilities provide team-wide buffs. Great support.\n"
            "**Turtle** - Ultimate tank with shield abilities.\n"
            "**Cat** - Agile with high crit chance.\n\n"
            "## C Tier\n"
            "**Rabbit** - Speed-focused with evasion. Niche.\n"
            "**Deer** - Support-oriented with healing.\n\n"
            "## Best Synergy Combos\n"
            "1. Wolf + Bear - Tanky pack\n"
            "2. Fox + Eagle - Burst damage\n"
            "3. Snake + Owl - Poison + wisdom\n\n"
            "Play free at [wilderkinleague.com](https://wilderkinleague.com).\n"
        ),
    },
    {
        "slug": "builds-guide",
        "filename": "wilderkin-league-builds-synergies-guide.md",
        "content": (
            "# Best Wilderkin League Builds and Synergies Guide\n\n"
            "## Build 1: Wolf Pack Rush\n"
            "4x Wolf + 2x Bear. Stack wolves for pack bonus.\n\n"
            "## Build 2: Poison Control\n"
            "3x Snake + 2x Owl + 1x Turtle. Apply poison, Owl buffs tick damage.\n\n"
            "## Build 3: Glass Cannon\n"
            "3x Fox + 2x Eagle + 1x Cat. Maximum burst damage.\n\n"
            "## Build 4: Immortal Fortress\n"
            "2x Turtle + 2x Bear + 2x Deer. Pure defense.\n\n"
            "## Build 5: Balanced Meta\n"
            "2x Wolf + 2x Fox + 1x Bear + 1x Owl. Most versatile.\n\n"
            "Try these at [wilderkinleague.com](https://wilderkinleague.com).\n"
        ),
    },
    {
        "slug": "abilities-guide",
        "filename": "wilderkin-league-all-abilities-explained.md",
        "content": (
            "# All Wilderkin League Species Abilities Explained\n\n"
            "95+ unique abilities across 10 species.\n\n"
            "**Wolf:** Pack Howl, Alpha Strike, Coordinated Hunt\n"
            "**Fox:** Trickster Dodge, Counter Strike, Illusion\n"
            "**Bear:** Endurance, Maul, Thick Hide\n"
            "**Eagle:** Aerial Dive, Keen Eyes, Wind Gust\n"
            "**Owl:** Wisdom Aura, Night Vision, Silent Flight\n"
            "**Snake:** Venom Fang, Toxic Cloud, Constrict\n"
            "**Turtle:** Shell Shield, Withdraw, Tidal Wave\n"
            "**Rabbit:** Quick Dash, Burrow, Lucky Foot\n"
            "**Deer:** Nature Blessing, Antler Charge, Forest Camouflage\n"
            "**Cat:** Critical Pounce, Nine Lives, Curiosity\n\n"
            "Play free at [wilderkinleague.com](https://wilderkinleague.com).\n"
        ),
    },
    {
        "slug": "beginner-guide",
        "filename": "how-to-win-wilderkin-league-beginner-guide.md",
        "content": (
            "# How to Win Wilderkin League - Beginner Guide\n\n"
            "## Getting Started\n"
            "Open [wilderkinleague.com](https://wilderkinleague.com). No download needed.\n\n"
            "## Basic Strategy\n"
            "- Save resources early\n"
            "- 2+ same species activates species bonus\n"
            "- Put tanks in front, damage dealers in back\n\n"
            "## Common Mistakes\n"
            "1. Spreading across too many species\n"
            "2. Ignoring positioning\n"
            "3. Never adapting to opponent\n\n"
            "## First Build: 4 Wolves + 2 Bears\n"
            "Simple pack synergy with tanky frontline.\n\n"
            "Play free at [wilderkinleague.com](https://wilderkinleague.com).\n"
        ),
    },
]


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"total_generated": 0, "total_runs": 0}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def cmd_generate():
    state = load_state()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = 0
    for page in SEO_PAGES:
        output_path = OUTPUT_DIR / page["filename"]
        print(f"Generating: {page['slug']}...")
        with open(output_path, "w") as f:
            f.write(page["content"])
        print(f"  Saved to {output_path}")
        generated += 1
    if generated > 0:
        state["total_generated"] = state.get("total_generated", 0) + generated
        state["total_runs"] = state.get("total_runs", 0) + 1
        save_state(state)
        print(f"\nGenerated {generated}/{len(SEO_PAGES)} SEO pages")
        print(f"Output saved to: {OUTPUT_DIR}")
        return 0
    return 1


def cmd_status():
    state = load_state()
    print(f"Total pages generated: {state.get('total_generated', 0)}")
    print(f"Total runs: {state.get('total_runs', 0)}")
    if OUTPUT_DIR.exists():
        files = list(OUTPUT_DIR.glob("*.md"))
        print(f"Files in seo_output/: {len(files)}")
        for f in files:
            print(f"  {f.name}")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "generate":
        sys.exit(cmd_generate())
    elif cmd == "status":
        sys.exit(cmd_status())
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
