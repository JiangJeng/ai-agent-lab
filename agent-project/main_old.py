import os
import sys
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google import genai
    from google.genai import types
except ImportError as e:
    print(f"Error: google-genai SDK not found. pip install -r requirements.txt")
    print(f"Import error: {e}")
    sys.exit(1)

def get_gemini_client():
    """Create and configure the Gemini client from the API key in env."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("Error: GEMINI_API_KEY not found.")
        sys.exit(1)
    
    # Only run this block for Gemini Developer API
    return genai.Client(api_key=api_key)

    # Only run this block for Gemini Enterprise Agent Platform API
    # return genai.Client(enterprise=True, project='your-project-id', location='us-central1')

def get_calculator_tool():
    """Return the calculator tool schema for Gemini function calling."""
    from calculator import get_calculator_tool_schema
    return get_calculator_tool_schema()

def execute_calculator(operation, a, b):
    """Execute calculator operation and return result dict."""
    from calculator import execute_calculator as calc
    return calc(operation, a, b)

def handle_tool_call(tool_name, args):
    """Dispatch a tool call to the appropriate handler."""
    if tool_name == "calculator":
        return execute_calculator(args["operation"], args["a"], args["b"])
    return {"error": "Unknown tool: " + tool_name}

def send_to_gemini(client, history, tools=None, model="gemini-3.8-flash"):
    """Send conversation history to Gemini and get a response."""
    try:
        contents = []
        for msg in history:
            role = msg.get("role")
            if role == "user":
                parts = []
                for p in msg.get("parts", []):
                    if isinstance(p, str):
                        parts.append(p)
                if parts:
                    contents.append({"role": "user", "parts": parts})
            elif role == "model":
                parts = []
                for p in msg.get("parts", []):
                    if isinstance(p, dict) and "functionCall" in p:
                        parts.append(p)
                    elif isinstance(p, dict) and "text" in p:
                        parts.append(p)
                if parts:
                    contents.append({"role": "model", "parts": parts})
        
        config = types.GenerateContentConfig(tools=tools)
        response = client.models.generate_content(model=model, contents=contents, config=config)
        return {"response": response, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}

def extract_function_call(response):
    """Extract function call info from a Gemini response."""
    function_calls=[]
    try:
        for fc in response.function_calls:
           function_calls.append({
                "name": fc.name,
                "args": dict(fc.args) if fc.args else {},
                "id": getattr(fc, "id", None)
            })
        return function_calls
    except Exception:
        pass
    return None

def extract_text(response):
    """Extract text content from a Gemini response."""
    try:
        return response.text or ""
    except Exception:
        return ""

def run_agent():
    """Main agent loop implementing the tool-calling flow."""
    print("=" * 60)
    print("Simple AI Agent with Gemini Tool-Calling")
    print("=" * 60)
    print()
    
    client = get_gemini_client()
    calculator_tool = get_calculator_tool()
    tools = [calculator_tool]
    history = []
    model = "gemini-3.8-flash"
    
    print(f"Using model: {model}")
    print(f"Available tool: calculator (add/subtract/multiply/divide)")
    print()
    print("Enter your query (type exit or quit to stop):")
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if not user_input:
            continue
        
        history.append(types.Content(role='user',parts=[types.Part.from_text(text=user_input)],))

        print("Agent thinking...")
        
        result = send_to_gemini(client, history, tools=tools)
        if not result["success"]:
            print(f"Error: {result['error']}")
            history.pop()
            continue
        
        response = result["response"]
        function_calls = extract_function_call(response)
        
        for fc in function_calls:
            tool_name = fc["name"]
            tool_args = fc["args"]
            
            print(f"Tool call: {tool_name}({tool_args})")
            
            #history.append({"role": "model", "parts": [{"function_call": {"name": tool_name, "args": tool_args, "id": function_call.get("id")}}]})

            history.append(response.candidates[0].content)
            function_response_part = types.Part.from_function_response(
               name=tool_name,
               response=tool_result,
               id=call_id,
           )
            
            function_call_part = response.function_calls

            tool_result = handle_tool_call(function_call_part.name, dict(function_call_part.args)
            print(f"Tool result: {tool_result}")
            
            history.append(
               types.Content(
                   role="user",
                   parts=[function_response_part]
               )
           )

            print("Reviewing tool result...")
            result2 = send_to_gemini(client, history, tools=tools)
            if not result2["success"]:
                print(f"Error: {result2['error']}")
                history.pop()
                continue
            final_text = extract_text(result2["response"])
            print(f"\nAgent: {final_text}")
        else:
            final_text = extract_text(response)
            print(f"\nAgent: {final_text}")
            history.append({"role": "model", "parts": [{"text": final_text}]})
    
    print("\nAgent session ended.")

if __name__ == "__main__":
    run_agent()
