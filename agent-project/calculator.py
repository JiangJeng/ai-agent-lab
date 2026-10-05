"""
Calculator Tool

A safe, structured calculator that can be invoked by an LLM.
The LLM selects the operation and provides two numeric operands.
"""

from typing import Literal


Operation = Literal[
    "add",
    "subtract",
    "multiply",
    "divide",
]


def get_calculator_tool_schema() -> dict:
    """
    Return the calculator tool schema used by Gemini.

    The schema tells the LLM:
    - what the tool does
    - when it should be used
    - what arguments are required
    """

    return {
        "name": "calculator",
        "description": (
            "Use this tool when an exact arithmetic calculation is required. "
            "Supported operations are add, subtract, multiply, and divide. "
            "Do not use this tool for general conversation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "add",
                        "subtract",
                        "multiply",
                        "divide",
                    ],
                    "description": (
                        "The arithmetic operation to perform."
                    ),
                },
                "a": {
                    "type": "number",
                    "description": "The first numeric operand.",
                },
                "b": {
                    "type": "number",
                    "description": "The second numeric operand.",
                },
            },
            "required": [
                "operation",
                "a",
                "b",
            ],
        },
    }


def execute_calculator(
    operation: Operation,
    a: float,
    b: float,
) -> dict:
    """
    Execute a calculator operation.

    Returns:
        {"result": value}
        or
        {"error": "..."}
    """

    # Runtime validation is still required even though
    # Operation is defined using Literal.
    if operation not in (
        "add",
        "subtract",
        "multiply",
        "divide",
    ):
        return {
            "error": (
                f"Invalid operation: {operation}. "
                "Must be one of: add, subtract, multiply, divide."
            )
        }

    try:
        if operation == "add":
            result = a + b

        elif operation == "subtract":
            result = a - b

        elif operation == "multiply":
            result = a * b

        elif operation == "divide":
            if b == 0:
                return {
                    "error": "Cannot divide by zero."
                }

            result = a / b

        return {
            "result": result
        }

    except (TypeError, ValueError) as e:
        return {
            "error": f"Calculation error: {e}"
        }
