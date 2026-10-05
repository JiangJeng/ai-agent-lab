"""
Calculator Tool Module

Defines a safe calculator tool that can be invoked by the LLM.
The calculator exposes structured operations (add, subtract, multiply, divide)
with proper error handling for invalid operations and division by zero.

Use this tool when an exact arithmetic calculation is required.
Do not use it for general conversation.
Supported operations are add, subtract, multiply, and divide.

"""

from typing import Literal

# Valid operations for the calculator tool
Operation = Literal["add", "subtract", "multiply", "divide"]


def get_calculator_tool_schema() -> dict:
    """
    Returns the tool schema for the calculator, designed for Gemini's function calling.
    
    Returns:
        dict: The tool definition with name, description, and parameters.
    """
    return {
        "name": "calculator",
        "description": (
            "Perform a basic arithmetic calculation. "
            "Useful for computing mathematical expressions involving addition, subtraction, multiplication, or division. "
            "For division, ensure the divisor (second number) is not zero."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The arithmetic operation to perform"
                },
                "a": {
                    "type": "number",
                    "description": "The first operand"
                },
                "b": {
                    "type": "number",
                    "description": "The second operand"
                }
            },
            "required": ["operation", "a", "b"]
        }
    }


def execute_calculator(
    operation: Operation,
    a: float,
    b: float
) -> dict:
    """
    Execute a calculator operation and return the result.
    
    Args:
        operation: One of "add", "subtract", "multiply", "divide"
        a: First operand
        b: Second operand
        
    Returns:
        dict: Contains "result" key with the computed value, or "error" key on failure
    """
    try:
        # Validate operation
        if operation not in ("add", "subtract", "multiply", "divide"):
            return {"error": f"Invalid operation: {operation}. Must be one of: add, subtract, multiply, divide"}
        
        # Perform the operation
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            # Explicitly handle division by zero
            if b == 0:
                return {"error": "Cannot divide by zero: divisor 'b' must not be 0"}
            result = a / b
        
        return {"result": result}
    
    except (TypeError, ValueError) as e:
        return {"error": f"Calculation error: {str(e)}"}
