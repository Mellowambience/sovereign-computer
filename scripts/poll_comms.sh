#!/usr/bin/env bash
# poll_comms.sh — Local poller for COMMS.md bridge
# Polls the repo every 30s. When SureThing drops a PENDING goal,
# this script runs it through sovereign_computer.py and commits the result back.
#
# Setup (one-time):
#   chmod +x scripts/poll_comms.sh
#   ./scripts/poll_comms.sh
#
# Or run as background daemon:
#   nohup ./scripts/poll_comms.sh &

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMMS_FILE="$REPO_DIR/COMMS.md"
ORCHESTRATOR="$REPO_DIR/sovereign_computer.py"
POLL_INTERVAL=30

echo "[poll_comms] Starting. Watching $COMMS_FILE every ${POLL_INTERVAL}s"
echo "[poll_comms] Repo: $REPO_DIR"

while true; do
  # Pull latest from remote
  cd "$REPO_DIR" && git pull --quiet origin main 2>/dev/null

  # Check if there's a PENDING task
  STATUS=$(grep -E '^STATUS:' "$COMMS_FILE" | awk '{print $2}')

  if [ "$STATUS" = "PENDING" ]; then
    GOAL=$(grep -E '^GOAL:' "$COMMS_FILE" | sed 's/^GOAL: //')
    SUBMITTED_AT=$(grep -E '^SUBMITTED_AT:' "$COMMS_FILE" | awk '{print $2}')

    echo "[poll_comms] PENDING task detected: $GOAL"
    echo "[poll_comms] Running sovereign_computer.py..."

    # Run the orchestrator, capture output
    RESULT=$(cd "$REPO_DIR" && python "$ORCHESTRATOR" --goal "$GOAL" 2>&1)
    EXIT_CODE=$?
    COMPLETED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    if [ $EXIT_CODE -eq 0 ]; then
      NEW_STATUS="DONE"
    else
      NEW_STATUS="ERROR"
    fi

    # Escape result for sed (replace newlines with \n literal)
    RESULT_ESCAPED=$(echo "$RESULT" | head -20 | tr '\n' ' ' | sed 's/\/\\\//g')

    # Write result back to COMMS.md
    cat > "$COMMS_FILE" << EOF
# COMMS.md — AI ↔ Sovereign Computer Bridge

This file is the zero-infrastructure communication channel between SureThing (remote AI) and your local Sovereign Computer stack.

## How it works

1. **SureThing pushes a goal** → commits a \`PENDING\` block to this file
2. **Your local machine polls** → detects \`PENDING\`, runs the goal via \`sovereign_computer.py\`
3. **Local machine writes result** → commits back to \`RESULT\` block
4. **SureThing reads result** → closes the loop

No open ports. No ngrok. No n8n. Just git.

---

## Current Task

\`\`\`
STATUS: $NEW_STATUS
GOAL: $GOAL
SUBMITTED_AT: $SUBMITTED_AT
RESULT: $RESULT_ESCAPED
COMPLETED_AT: $COMPLETED_AT
\`\`\`

---

## Protocol

### SureThing writes (when submitting a goal):
\`\`\`
STATUS: PENDING
GOAL: <natural language goal>
SUBMITTED_AT: <ISO timestamp>
RESULT: (none)
COMPLETED_AT: (none)
\`\`\`

### Local poller writes (when done):
\`\`\`
STATUS: DONE
GOAL: <original goal>
SUBMITTED_AT: <original timestamp>
RESULT: <output or path to output file>
COMPLETED_AT: <ISO timestamp>
\`\`\`

### On error:
\`\`\`
STATUS: ERROR
RESULT: <error message>
\`\`\`
EOF

    # Commit result back
    cd "$REPO_DIR"
    git add COMMS.md
    git commit -m "result: [$NEW_STATUS] $GOAL" --quiet
    git push origin main --quiet

    echo "[poll_comms] Done. Status: $NEW_STATUS. Result committed."
  fi

  sleep $POLL_INTERVAL
done
