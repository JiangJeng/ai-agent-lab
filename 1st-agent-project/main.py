"""An educational Gemini agent with an explicit tool-calling loop."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from calculator import CALCULATOR_DECLARATION, calculator


def execute_tool(call) -> dict:
    """Validate a model-requested tool call before executing it."""
    if call.name != "calculator":
        return {"error": "Unknown tool. Only calculator is available."}
    arguments = call.args
    if not isinstance(arguments, dict) or set(arguments) != {"operation", "a", "b"}:
        return {"error": "Calculator requires exactly operation, a, and b."}
    return calculator(**arguments)


def run_agent(prompt: str, client: genai.Client, model: str) -> str:
    """Let the LLM choose tools, execute them, then ask the LLM for an answer."""
    if not prompt.strip():
        raise ValueError("Please enter a non-empty question.")
    history = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are a helpful assistant. Use calculator for arithmetic. "
            "For compound calculations, use multiple calculator calls. "
            "Answer other questions normally. If a tool returns an error, "
            "explain it to the user; never invent a successful result."
        ),
        tools=[types.Tool(function_declarations=[CALCULATOR_DECLARATION])],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    for _ in range(5):
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model, contents=history, config=config
                )
                if not response.candidates or response.candidates[0].content is None:
                    raise RuntimeError("Gemini returned no usable content (possibly blocked).")
            except genai.ApiError as exc:   
                raise RuntimeError(
                    f"Gemini request failed ({exc.status_code}): {exc.message}"
                ) from exc
            except ServerError as exc:
                # Retry on server errors(5xx), which may be transient. 
                wait_time = 2 ** attempt # Exponential backoff: 1, 2, 4 seconds
                print(f"Server error ({exc.status_code}). Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            except ClientError as exc:
                # Client errors (4xx) are usually not recoverable, so we raise immediately.
                print(f"Client error ({exc.status_code}): {exc.message}. Not retrying.")
                raise exc
        
        # Preserve the original content, including any thought signatures.
        model_content = response.candidates[0].content
        history.append(model_content)
        calls = [
            part.function_call
            for part in (model_content.parts or [])
            if part.function_call is not None
        ]
        if not calls:
            answer = "".join(
                part.text
                for part in (model_content.parts or [])
                if part.text and not part.thought
            )
            if not answer.strip():
                raise RuntimeError("Gemini returned no final text answer.")
            return answer

        results = []
        for call in calls:
            result = execute_tool(call)
            print(f"[tool] {call.name}: {result}")
            result_part = types.Part.from_function_response(
                name=call.name or "unknown", response=result
            )
            # The helper accepts no id argument; the response object does.
            result_part.function_response.id = call.id
            results.append(result_part)
        history.append(types.Content(role="user", parts=results))

    raise RuntimeError("Tool-calling limit reached without a final answer.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", help="Ask a question without the input prompt.")
    args = parser.parse_args()
    # Load only this project's .env; never load the sibling project's secrets.
    load_dotenv(Path(__file__).resolve().parent / ".env")
    if os.getenv("LLM_PROVIDER", "gemini").strip().lower() != "gemini":
        print("Error: this first version supports only LLM_PROVIDER=gemini.", file=sys.stderr)
        return 1
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        print("Error: set GEMINI_API_KEY in your environment or local .env.", file=sys.stderr)
        return 1

    try:
        prompt = args.prompt if args.prompt is not None else input("You: ")
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        if not model:
            raise ValueError("GEMINI_MODEL must not be empty.")
        with genai.Client(api_key=api_key) as client:
            print(f"Agent: {run_agent(prompt, client, model)}")
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        return 130
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    
    except Exception as exc:
        # Do not print API request details, which could contain credentials.
        print(
            f"Error: Gemini request failed ({type(exc).__name__}). "
            "Check your API key, model, quota, and network connection.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
