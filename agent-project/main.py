import os
import sys

from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError as e:
    print("Error: google-genai SDK not found.")
    print("Please run: pip install -r requirements.txt")
    print(f"Import error: {e}")
    sys.exit(1)


MODEL = "gemini-3.8-flash"


def get_gemini_client():
    """Create the Gemini client using GEMINI_API_KEY."""
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key or api_key == "your_gemini_api_key_here":
        print("Error: GEMINI_API_KEY not found.")
        print("Please check your .env file.")
        sys.exit(1)

    return genai.Client(api_key=api_key)


def get_calculator_tool():
    """Return the calculator tool schema."""
    from calculator import get_calculator_tool_schema

    return get_calculator_tool_schema()


def execute_calculator(operation, a, b):
    """Execute the calculator tool."""
    from calculator import execute_calculator

    return execute_calculator(operation, a, b)


def handle_tool_call(tool_name, args):
    """
    Dispatch a tool call to the correct Python function.

    This is the bridge between the LLM and our local tools.
    """
    if tool_name == "calculator":
        try:
            return execute_calculator(
                operation=args["operation"],
                a=args["a"],
                b=args["b"],
            )
        except KeyError as e:
            return {
                "error": f"Missing required calculator argument: {e}"
            }
        except Exception as e:
            return {
                "error": f"Calculator error: {e}"
            }

    return {
        "error": f"Unknown tool: {tool_name}"
    }


def send_to_gemini(client, history, tools):
    """
    Send the current conversation history to Gemini.

    The history contains native google-genai Content objects.
    """
    try:
        config = types.GenerateContentConfig(
            tools=tools
        )

        response = client.models.generate_content(
            model=MODEL,
            contents=history,
            config=config,
        )

        return {
            "success": True,
            "response": response,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def extract_function_calls(response):
    """
    Return all function calls requested by Gemini.

    A response may contain zero, one, or multiple function calls.
    """
    return response.function_calls or []


def extract_text(response):
    """Extract Gemini's text response safely."""
    try:
        return response.text or ""
    except Exception:
        return ""


def run_agent():
    """Run the interactive Gemini tool-calling agent."""

    print("=" * 60)
    print("Simple AI Agent with Gemini Tool-Calling")
    print("=" * 60)
    print()

    client = get_gemini_client()

    calculator_tool = get_calculator_tool()
    tools = [calculator_tool]

    # Conversation history uses native google-genai Content objects.
    history = []

    print(f"Using model: {MODEL}")
    print("Available tool: calculator")
    print()
    print("Enter your query (type exit or quit to stop):")

    while True:

        user_input = input("\nYou: ").strip()

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        if not user_input:
            continue

        # ---------------------------------------------------------
        # 1. Add user's message to conversation history
        # ---------------------------------------------------------
        history.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_input)
                ],
            )
        )

        print("Agent thinking...")

        # ---------------------------------------------------------
        # 2. Agent Loop
        #
        # Gemini may:
        #   a) answer directly
        #   b) request one or more tools
        #
        # If tools are requested, execute them and call Gemini again.
        # ---------------------------------------------------------
        while True:

            result = send_to_gemini(
                client=client,
                history=history,
                tools=tools,
            )

            if not result["success"]:
                print(f"Error: {result['error']}")

                # Remove the user's latest message if the request failed.
                history.pop()
                break

            response = result["response"]

            function_calls = extract_function_calls(response)

            # -----------------------------------------------------
            # 3. No tool call -> final answer
            # -----------------------------------------------------
            if not function_calls:

                final_text = extract_text(response)

                print(f"\nAgent: {final_text}")

                # Preserve Gemini's actual response Content.
                if response.candidates:
                    history.append(
                        response.candidates[0].content
                    )

                break

            # -----------------------------------------------------
            # 4. Gemini requested one or more tools.
            #
            # IMPORTANT:
            # Preserve Gemini's original response Content.
            # Do NOT manually reconstruct the function-call message.
            # 把 LLM 刚才说的话原封不动记下来。
            # -----------------------------------------------------
            if response.candidates:
                history.append(
                    response.candidates[0].content
                )

            # -----------------------------------------------------
            # 5. Execute ALL function calls
            # -----------------------------------------------------
            function_response_parts = []

            for function_call in function_calls:

                tool_name = function_call.name
                tool_args = dict(function_call.args or {})
                call_id = getattr(function_call, "id", None)

                print(
                    f"Tool call: "
                    f"{tool_name}({tool_args})"
                )

                # Execute the actual Python function.
                # Agent 根据 LLM 的要求，真正执行 Python Tool。
                tool_result = handle_tool_call(
                    tool_name,
                    tool_args,
                )

                print(f"Tool result: {tool_result}")

                # -------------------------------------------------
                # Convert Python result into a Gemini
                # function-response Part.
                # 把 Tool 的结果包装成 LLM 能理解的 Function Response。
                # -------------------------------------------------
                function_response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response=tool_result,
                        id=call_id,
                    )
                )

            # -----------------------------------------------------
            # 6. Send ALL tool results back to Gemini.
            #
            # This becomes the next turn of the Agent Loop.
            # 把 Tool Result 送回 LLM，让 LLM 决定下一步。
            # -----------------------------------------------------
            history.append(
                types.Content(
                    role="user",
                    parts=function_response_parts,
                )
            )

            print("Reviewing tool result...")


if __name__ == "__main__":
    run_agent()