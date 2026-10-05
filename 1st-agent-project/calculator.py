"""A structured calculator: no expression parsing or eval."""

import math

# ---------------------------------------------------------------------------
# FUNCTION DECLARATION (Tool Schema)
# Gemini reads this OpenAPI/JSON-Schema definition to learn that this tool
# exists, what arguments it accepts, and how to structure calls to it.
# ---------------------------------------------------------------------------
CALCULATOR_DECLARATION = {
    "name": "calculator",  # Unique name Gemini will reference in tool calls
    "description": "Calculate one arithmetic operation on two finite numbers.",
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                # Restricts Gemini to only picking one of these 4 exact string values
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "The operation to perform on a and b, in that order.",
            },
            "a": {"type": "number", "description": "First operand."},
            "b": {"type": "number", "description": "Second operand."},
        },
        # Tells Gemini that all 3 arguments must be supplied for every call
        "required": ["operation", "a", "b"],
    },
}


# ---------------------------------------------------------------------------
# LOCAL EXECUTION FUNCTION
# This is the actual Python function executed on your machine when Gemini
# requests a "calculator" tool call.
# ---------------------------------------------------------------------------
def calculator(operation: str, a: float, b: float) -> dict:
    """Return a result or a safe error that can be sent back to the model."""
    
    # 1. Validate that operation is supported
    if operation not in ("add", "subtract", "multiply", "divide"):
        return {"error": "Unsupported operation. Use add, subtract, multiply, or divide."}
    
    # 2. Validate input types and check for edge cases (e.g., booleans, NaN, Infinity)
    for value in (a, b):
        # Python booleans (True/False) inherit from int; filter them out
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return {"error": "Operands must be finite numbers."}
        try:
            if not math.isfinite(value):
                return {"error": "Operands must be finite numbers."}
        except OverflowError:
            return {"error": "Operand is too large."}
            
    # 3. Guard against division by zero
    if operation == "divide" and b == 0:
        return {"error": "Division by zero is not allowed."}

    # 4. Perform calculation safely
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        else:
            result = a / b
            
        # Check if mathematical output resulted in Infinity or NaN
        if not math.isfinite(result):
            return {"error": "Result is too large to represent as a finite number."}
    except OverflowError:
        return {"error": "Result is too large to represent as a finite number."}

    # 5. Return structured dictionary back to Gemini via main.py
    return {"result": result}