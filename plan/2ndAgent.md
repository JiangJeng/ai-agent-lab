# 2ndAgent Project Plan

## Primary Objectives

### 1. Build a ReAct Engine
Create a loop that logs the reasoning flow in the console as:

- Thought
- Action
- Observation

This continues until the agent produces a final answer.

### 2. Add SQLite Persisted Memory
Introduce a tool named `notes_memory` backed by a local SQLite database file, `agent_memory.db`, so that data persists even after restarting the script.

### 3. Handle Multi-Step Compound Tasks
Force the agent to perform sequential tool calls, such as:

> Calculate `12 + 45`, multiply the result by `2`, save the answer in memory as `project_budget`, then retrieve `project_budget` and confirm what is stored.

---

## Planned Project Structure

```text
2ndAgent/
├── main.py              # Main ReAct loop engine and CLI runner
├── database.py          # SQLite helper routines for create/read/write operations
├── tools/
│   ├── __init__.py      # Tool registration and execution dispatcher
│   ├── calculator.py    # Math tool schema and logic
│   └── memory.py        # Key-value memory tool using SQLite
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```