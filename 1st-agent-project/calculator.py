"""A structured calculator: no expression parsing or eval."""

import math


CALCULATOR_DECLARATION = {
    "name": "calculator",
    "description": "Calculate one arithmetic operation on two finite numbers.",
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "The operation to perform on a and b, in that order.",
            },
            "a": {"type": "number", "description": "First operand."},
            "b": {"type": "number", "description": "Second operand."},
        },
        "required": ["operation", "a", "b"],
    },
}


def calculator(operation: str, a: float, b: float) -> dict:
    """Return a result or a safe error that can be sent back to the model."""
    if operation not in ("add", "subtract", "multiply", "divide"):
        return {"error": "Unsupported operation. Use add, subtract, multiply, or divide."}
    for value in (a, b):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return {"error": "Operands must be finite numbers."}
        try:
            if not math.isfinite(value):
                return {"error": "Operands must be finite numbers."}
        except OverflowError:
            return {"error": "Operand is too large."}
    if operation == "divide" and b == 0:
        return {"error": "Division by zero is not allowed."}

    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        else:
            result = a / b
        if not math.isfinite(result):
            return {"error": "Result is too large to represent as a finite number."}
    except OverflowError:
        return {"error": "Result is too large to represent as a finite number."}
    return {"result": result}
