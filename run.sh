#!/bin/bash
WORKDIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$WORKDIR/wilderkin.log"
API="http://localhost:8090"
PROJECT_ID="wilderkin"

# Load credentials from PM secrets API (preferred) or env files
# NOTE: Social media accounts MUST use usesnapapi.com emails, NOT unstableentity.com
eval "$(curl -s http://localhost:8090/api/secrets/env 2>/dev/null)" || true
for f in ~/.config/unstable-entity/*.env; do
    set -a; source "$f" 2>/dev/null || true; set +a
done

log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

cd "$WORKDIR"

REDDIT_POSTS=0
FEDI_POSTS=0
HN_POSTS=0
BSKY_POSTS=0
DEVTO_POSTS=0
TOTAL_FAILED=0

run_poster() {
    local name="$1"
    local script="$2"
    local args="${3:-}"

    if [ ! -f "$WORKDIR/$script" ]; then
        log "$name: script not found ($script)"
        return
    fi

    log "Running $name"
    OUTPUT=$(python3 "$script" $args 2>&1)
    EXIT=$?
    echo "$OUTPUT" >> "$LOG"

    if [ $EXIT -eq 0 ]; then
        POSTS=$(echo "$OUTPUT" | grep -ci "posted\|published\|submitted\|success" | tr -d '[:space:]')
        POSTS=${POSTS:-0}
        log "$name: $POSTS posts, exit 0"
        return $POSTS
    else
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        log "$name: failed (exit $EXIT)"
        return 0
    fi
}

log "=== Wilderkin League marketing run ==="

# Reddit
run_poster "Reddit" "reddit_poster.py" "post"
REDDIT_POSTS=$?

# Mastodon
run_poster "Mastodon" "mastodon_poster.py" "post"
FEDI_POSTS=$?

# Hacker News
run_poster "HN" "hn_poster.py" "submit"
HN_POSTS=$?

# Bluesky
run_poster "Bluesky" "bluesky_poster.py" "post"
BSKY_POSTS=$?

# Dev.to
run_poster "Dev.to" "devto_poster.py" "post"
DEVTO_POSTS=$?

# Platform submissions
run_poster "Platforms" "platforms_submitter.py" "submit"

# SEO content generation
run_poster "SEO" "seo_content_generator.py" "generate"

TOTAL=$((REDDIT_POSTS + FEDI_POSTS + HN_POSTS + BSKY_POSTS + DEVTO_POSTS))
log "Done: reddit=$REDDIT_POSTS fedi=$FEDI_POSTS hn=$HN_POSTS bsky=$BSKY_POSTS devto=$DEVTO_POSTS total=$TOTAL failures=$TOTAL_FAILED"

# Report to PM API
curl -s -X PATCH "$API/api/projects/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d "{\"last_run_at\": \"$(date -u +%Y-%m-%dT%H:%M:%S)\", \"last_run_summary\": \"$TOTAL posts, $TOTAL_FAILED failures\"}" > /dev/null 2>&1

curl -s -X POST "$API/api/projects/$PROJECT_ID/kpis" \
  -H "Content-Type: application/json" \
  -d "{\"key\": \"Reddit posts\", \"value\": \"$REDDIT_POSTS\", \"unit\": \"kpl\"}" > /dev/null 2>&1

curl -s -X POST "$API/api/projects/$PROJECT_ID/kpis" \
  -H "Content-Type: application/json" \
  -d "{\"key\": \"Fediverse posts\", \"value\": \"$FEDI_POSTS\", \"unit\": \"kpl\"}" > /dev/null 2>&1

curl -s -X POST "$API/api/projects/$PROJECT_ID/kpis" \
  -H "Content-Type: application/json" \
  -d "{\"key\": \"Total reach\", \"value\": \"$TOTAL\", \"unit\": \"posts\"}" > /dev/null 2>&1

if [ "$TOTAL" -gt 0 ]; then
    curl -s -X POST "$API/api/projects/$PROJECT_ID/achievements" \
      -H "Content-Type: application/json" \
      -d "{\"achievement\": \"Posted $TOTAL across platforms (R:$REDDIT_POSTS M:$FEDI_POSTS HN:$HN_POSTS)\", \"phase\": \"production\"}" > /dev/null 2>&1
fi
