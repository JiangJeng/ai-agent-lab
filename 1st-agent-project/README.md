# First Gemini agent

A minimal educational agent using the official `google-genai` SDK directly.
No LangChain, LangGraph, MCP, provider factory, or expression evaluation.
The sibling `agent-project` is independent and is not used or modified.

## Files

```text
1st-agent-project/
  main.py          # Gemini requests, tool dispatch, and command-line entry point
  calculator.py    # Structured calculator and explicit tool schema
  test_agent.py    # Offline tests and mocked CLI demonstrations
  requirements.txt
  .env.example     # Placeholder configuration, not a real key
  .gitignore
  README.md
  .venv/           # Local virtual environment, ignored by Git
```

## Setup

Python 3.10+ is required. Run these commands from this folder.

Windows Git Bash (the IntelliJ terminal in this workspace):

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

On macOS/Linux, use `source .venv/bin/activate` instead.
In IntelliJ, select this folder's `.venv/Scripts/python.exe` as the interpreter
on Windows, or `.venv/bin/python` on macOS/Linux.

Provide `GEMINI_API_KEY` through your environment or IntelliJ run configuration.
Alternatively, copy `.env.example` to `.env` and set your key locally. No real
key or `.env` is supplied by this project. Do not paste keys into chat or source.

Optional environment variables:

- `GEMINI_MODEL`: defaults to `gemini-2.5-flash`; choose a model available to
  your account that supports function calling.
- `LLM_PROVIDER`: defaults to `gemini`. Other providers are explicitly rejected
  in this first version; this setting is only a placeholder for future work.

The application loads only this folder's `.env`, never the sibling project's
configuration. Already-set environment variables take precedence.

## Run

```bash
python main.py
# Or supply one question directly:
python main.py --prompt "What is an AI agent?"
```

Each run handles one question and exits. Tool executions appear as `[tool]`
lines so that the flow is visible. No cross-run chat history is stored.

## Complete tool-calling flow

1. **User → LLM:** Send the question and the calculator's JSON schema to Gemini.
2. **LLM → tool call:** Gemini decides whether to emit a `calculator` function
   call. There is no keyword-based or rule-based tool selection in Python.
3. **Tool execution:** Validate the name and argument shape, then call
   `calculator(operation, a, b)`. Supported operations are `add`, `subtract`,
   `multiply`, and `divide`. Operands must be finite numbers, not booleans or
   strings. No arbitrary expression is accepted or evaluated.
4. **Tool result → LLM:** Append the original model content unchanged (including
   thought signatures), then send `Part.from_function_response` results in a
   user-role content message. Preserve function-call IDs when provided.
5. **LLM → final answer:** Gemini explains the result or tool error. Additional
   tool calls repeat the loop, with an eight-request safety limit.

Automatic SDK function execution is explicitly disabled: the Python loop is
responsible for executing and returning every tool call. A normal question
typically returns directly at step 2 without calling the calculator.

## Offline tests

1. Complete [Setup](#setup) to create the virtual environment and install the
   dependencies. No API key is needed for offline tests.
2. Open a terminal in `1st-agent-project` and activate the environment. In
   Windows Git Bash:

   ```bash
   source .venv/Scripts/activate
   ```

   On macOS/Linux, use `source .venv/bin/activate` instead.
3. Run all tests and the mocked CLI demonstrations:

   ```bash
   python test_agent.py
   ```

   Expect `Ran 14 tests` and `OK`, followed by
   `CLI DEMOS WITH MOCKED SDK RESPONSES (not live Gemini)`. The demonstrations
   show a normal answer about Paris, multiplication returning `100`, and a
   division-by-zero error. Only the calculator demonstrations print `[tool]`
   lines. A test or demonstration failure produces a nonzero exit status.
4. To run only the tests, without demonstrations:

   ```bash
   python -m unittest -v test_agent
   ```

   To isolate one test, for example multiplication:

   ```bash
   python -m unittest -v test_agent.AgentTests.test_multiplication
   ```

The suite covers normal answers, all four calculator operations, invalid
numbers and calls, overflow, division by zero, multiple tool calls, preserved
thought signatures and call IDs, empty prompts/responses, the request limit,
missing keys, unsupported providers, and API-error redaction. SDK responses
are mocked: no network access is needed and no `.env` is loaded. The SDK must
still be installed because the tests use its response types.

## Required live demonstrations

After the offline checks pass, keep the virtual environment activated and run
these commands from `1st-agent-project`. These checks require your own valid
`GEMINI_API_KEY` configured as described in [Setup](#setup), network access,
and available quota. Unlike the offline tests, these commands contact Gemini
and load this folder's `.env` if present.

1. Check a normal answer without a tool call:

   ```bash
   python main.py --prompt "What is the capital of France?"
   ```

   Expect an answer about Paris, with no `[tool]` line.
2. Check successful calculator execution:

   ```bash
   python main.py --prompt "Use the calculator to multiply 25 by 4."
   ```

   Expect a `[tool]` line returning `{'result': 100}`, followed by Gemini's
   answer.
3. Check calculator error handling:

   ```bash
   python main.py --prompt "Use the calculator to divide 10 by 0."
   ```

   Expect a `[tool]` line returning
   `{'error': 'Division by zero is not allowed.'}`, followed by Gemini
   explaining the error rather than claiming a result. A handled tool error
   is a successful demonstration, not an application failure.

Gemini's exact wording and decisions can vary. Mocked SDK responses can test
the Python flow without credentials, but cannot prove live Gemini behavior.

## Errors and secrets

Missing keys, unsupported providers, empty input, unusable responses, and
excessive tool calls produce a clear failure and nonzero exit status. Tool
validation errors are returned to the LLM so it can explain them. API/network
failures produce a generic message without dumping credential-bearing requests.

`.gitignore` excludes `.env`, local environment variants, virtual environments,
local libraries, IDE metadata, caches, and build output. `.env.example` remains
trackable. Git ignore rules prevent normal accidental additions, not
`git add --force` or commits of files that were already tracked. Never force-add
secrets; rotate a key if it has been exposed.
