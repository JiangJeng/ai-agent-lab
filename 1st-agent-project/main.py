"""An educational Gemini agent with an explicit tool-calling loop."""

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

# Import the custom calculator function and its JSON metadata schema declaration
from calculator import CALCULATOR_DECLARATION, calculator


def execute_tool(call) -> dict:
    """Validate a model-requested tool call before executing it.
    
    The LLM outputs a function name and arguments. This function acts as a local security 
    and validation layer before running local Python code.
    """
    # Verify that the LLM requested a known tool name
    if call.name != "calculator":
        return {"error": "Unknown tool. Only calculator is available."}
    
    arguments = call.args
    # Verify that the LLM provided all expected argument keys
    if not isinstance(arguments, dict) or set(arguments) != {"operation", "a", "b"}:
        return {"error": "Calculator requires exactly operation, a, and b."}
    
    # Safely unpack the validated arguments and execute the actual Python function
    return calculator(**arguments)


def run_agent(prompt: str, client: genai.Client, model: str) -> str:
    """Let the LLM choose tools, execute them, then ask the LLM for an answer.
    
    This function coordinates the multi-turn agent execution loop.
    """
    if not prompt.strip():
        raise ValueError("Please enter a non-empty question.")
    
    # 1. Initialize conversation history with the user's initial prompt
    history = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    
    # 2. Configure the agent instructions, available tools, and function calling mode
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are a helpful assistant. Use calculator for arithmetic. "
            "For compound calculations, use multiple calculator calls. "
            "Answer other questions normally. If a tool returns an error, "
            "explain it to the user; never invent a successful result."
        ),
        # Pass the tool schema to Gemini so it knows what functions are available
        tools=[types.Tool(function_declarations=[CALCULATOR_DECLARATION])],
        # Disable automatic function calling so we can explicitly handle the loop manually
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    # Agent Execution Loop: Allows up to 5 tool-use iterations to solve complex tasks
    for _ in range(5):
        # Retry Loop: Handles transient network/server errors when contacting Gemini
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model, contents=history, config=config
                )
                if not response.candidates or response.candidates[0].content is None:
                    raise RuntimeError("Gemini returned no usable content (possibly blocked).")
                break # Request succeeded, exit retry loop
            except ServerError as exc:
                # Retry on server errors (5xx), which may be transient. 
                wait_time = 2 ** attempt # Exponential backoff: 1, 2, 4 seconds
                print(f"Server error ({exc.status_code}). Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            except ClientError as exc:
                # Client errors (4xx) are usually not recoverable (e.g. bad API key), raise immediately.
                print(f"Client error ({exc.status_code}): {exc.message}. Not retrying.")
                raise exc
        
        # Preserve the model's output content (including reasoning and tool call requests)
        model_content = response.candidates[0].content
        # Append Gemini's response into the conversation history
        history.append(model_content)
        
        # Check if Gemini requested any tool/function calls in this response turn
        calls = [
            part.function_call
            for part in (model_content.parts or [])
            if part.function_call is not None
        ]
        
        # IF NO TOOL CALLS REQUESTED: Gemini has calculated its final answer
        if not calls:
            answer = "".join(
                part.text
                for part in (model_content.parts or [])
                if part.text and not part.thought
            )
            if not answer.strip():
                raise RuntimeError("Gemini returned no final text answer.")
            return answer # Return final text response to the user

        # IF TOOL CALLS REQUESTED: Execute the requested tools locally
        results = []
        for call in calls:
            result = execute_tool(call) # Run local Python code
            print(f"[tool] {call.name}: {result}")
            
            # Convert execution result into Gemini's function response format
            result_part = types.Part.from_function_response(
                name=call.name or "unknown", response=result
            )
            # Link response back to the specific function call ID requested by Gemini
            result_part.function_response.id = call.id
            results.append(result_part)
            
        # Append tool execution results back to history as a user role message
        # This sends the calculation results back to Gemini for the next loop turn
        history.append(types.Content(role="user", parts=results))

    raise RuntimeError("Tool-calling limit reached without a final answer.")


def main() -> int:
    # Set up command-line argument parsing (allows passing --prompt "...")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", help="Ask a question without the input prompt.")
    args = parser.parse_args()
    
    # Load environment variables from the local .env file
    load_dotenv(Path(__file__).resolve().parent / ".env")
    
    # Validate provider configuration
    if os.getenv("LLM_PROVIDER", "gemini").strip().lower() != "gemini":
        print("Error: this first version supports only LLM_PROVIDER=gemini.", file=sys.stderr)
        return 1
        
    # Check that GEMINI_API_KEY is configured
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        print("Error: set GEMINI_API_KEY in your environment or local .env.", file=sys.stderr)
        return 1

    try:
        # Obtain user prompt from argument flag or interactive input prompt
        prompt = args.prompt if args.prompt is not None else input("You: ")
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        if not model:
            raise ValueError("GEMINI_MODEL must not be empty.")
            
        # Context manager handles initialising and cleaning up client connection
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
        # Fallback catch-all error handler (prevents leaking secrets in logs)
        print(
            f"Error: Gemini request failed ({type(exc).__name__}). "
            "Check your API key, model, quota, and network connection.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())