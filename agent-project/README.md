# Simple AI Agent with Gemini Tool-Calling

A minimal Python AI agent project that demonstrates **LLM tool-calling** using Google Gemini.

## Architecture

```
User → LLM → Tool Call → Calculator Tool → Tool Result → LLM → Final Answer
```
LLM
 ↓
Tool Selection
 ↓
Structured Arguments
 ↓
Local Function
 ↓
Structured Result
 ↓
LLM

## Features

- Uses the official `google-genai` SDK (not legacy `google-generativeai`)
- Structured calculator tool: `calculator(operation, a, b)` where operation is one of `add`, `subtract`, `multiply`, `divide`
- LLM decides when to call the calculator (no keyword/rule-based detection)
- Proper error handling for division by zero and invalid operations
- No external agent frameworks (LangChain, LangGraph, MCP, etc.)

## Project Structure

```
agent-project/
├── main.py              # Agent core: conversation loop + LLM orchestration + tool dispatch
├── calculator.py        # Calculator tool: schema + execution with validation
├── requirements.txt     # Python dependencies
├── .env.example         # Template for environment variables
├── .gitignore           # Excludes .env and other sensitive files
└── README.md            # This file
```

## Setup

### 1. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure your API key
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

Get a Gemini API key at: https://ai.google.dev

## Usage

```bash
python main.py
```

Then type queries like:
- Normal question: "What is 2+2?" → Agent uses LLM to reason and call calculator
- Multiplication: "What is 7 times 8?" → LLM decides to call calculator with multiply
- Division by zero: "What is 5 divided by 0?" → Calculator returns an error, LLM responds gracefully

## How It Works
main.py
     │
     ├── Tool Schema
     │
     ├── Tool Dispatcher
     │
     └── Agent Loop
              │
              ↓
       calculator.py
              │
              └── execute_calculator()

1. **User input** is added to conversation history
2. **Agent sends** history + tool definitions to Gemini
3. **Gemini returns** either a text response or a function call
4. **If tool call**: Agent executes the calculator, appends result to history, and calls Gemini again
5. **If text**: Agent prints the response and continues the loop

              ┌─────────────┐
              │    User     │
              └──────┬──────┘
                     ↓
              ┌─────────────┐
        ┌────→│    Gemini   │
        │     └──────┬──────┘
        │            │
        │       Function Call
        │            ↓
        │     ┌─────────────┐
        │     │ Python Tool │
        │     └──────┬──────┘
        │            │
        │       Tool Result
        │            ↓
        │     ┌─────────────┐
        └─────│    Gemini   │
              └──────┬──────┘
                     │
              Function Call?
                /         \
              Yes          No
               │            │
               └─── loop    ↓
                       Final Answer
                       
## Tools

The calculator tool supports:
- `add(a, b)` → a + b
- `subtract(a, b)` → a - b
- `multiply(a, b)` → a × b
- `divide(a, b)` → a ÷ b (with division-by-zero protection)

## Future Extensions

- Add more tools (weather, search, etc.)
- Support multiple LLM providers (OpenAI, Anthropic, Ollama)
- Add conversation persistence
