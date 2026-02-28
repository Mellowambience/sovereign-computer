# COMMS.md — AI ↔ Sovereign Computer Bridge

This file is the zero-infrastructure communication channel between SureThing (remote AI) and your local Sovereign Computer stack.

## How it works

1. **SureThing pushes a goal** → commits a `PENDING` block to this file
2. **Your local machine polls** → detects `PENDING`, runs the goal via `sovereign_computer.py`
3. **Local machine writes result** → commits back to `RESULT` block
4. **SureThing reads result** → closes the loop

No open ports. No ngrok. No n8n. Just git.

---

## Current Task

```
STATUS: IDLE
GOAL: (none)
SUBMITTED_AT: (none)
RESULT: (none)
COMPLETED_AT: (none)
```

---

## Protocol

### SureThing writes (when submitting a goal):
```
STATUS: PENDING
GOAL: <natural language goal>
SUBMITTED_AT: <ISO timestamp>
RESULT: (none)
COMPLETED_AT: (none)
```

### Local poller writes (when done):
```
STATUS: DONE
GOAL: <original goal>
SUBMITTED_AT: <original timestamp>
RESULT: <output or path to output file>
COMPLETED_AT: <ISO timestamp>
```

### On error:
```
STATUS: ERROR
RESULT: <error message>
```
