"""Offline tests and demos: no real API key, .env access, or network requests."""

import contextlib
import io
import os
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

from google.genai import types

import main
from calculator import calculator


def text_response(answer):
    return types.GenerateContentResponse(candidates=[types.Candidate(
        content=types.Content(role="model", parts=[types.Part(text=answer)])
    )])


def tool_response(operation="multiply", a=25, b=4, call_id="test-call"):
    part = types.Part(
        function_call=types.FunctionCall(
            name="calculator",
            args={"operation": operation, "a": a, "b": b},
            id=call_id,
        ),
        thought_signature=b"original-signature",
    )
    return types.GenerateContentResponse(candidates=[types.Candidate(
        content=types.Content(role="model", parts=[part])
    )])


def mock_client(*responses):
    client = Mock()
    client.models.generate_content.side_effect = list(responses)
    return client


class AgentTests(unittest.TestCase):
    def run_quietly(self, client, prompt="Question"):
        with contextlib.redirect_stdout(io.StringIO()):
            return main.run_agent(prompt, client, "test-model")

    def test_normal_question(self):
        client = mock_client(text_response("Paris"))
        with contextlib.redirect_stdout(io.StringIO()) as output:
            answer = main.run_agent("What is the capital of France?", client, "test-model")
        self.assertEqual(answer, "Paris")
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(client.models.generate_content.call_count, 1)
        config = client.models.generate_content.call_args.kwargs["config"]
        self.assertTrue(config.automatic_function_calling.disable)
        self.assertEqual(config.tools[0].function_declarations[0].name, "calculator")

    def test_multiplication(self):
        first = tool_response()
        client = mock_client(first, text_response("100"))
        self.assertEqual(self.run_quietly(client), "100")
        self.assertEqual(client.models.generate_content.call_count, 2)
        history = client.models.generate_content.call_args.kwargs["contents"]
        self.assertIs(history[1], first.candidates[0].content)
        self.assertEqual(history[1].parts[0].thought_signature, b"original-signature")
        self.assertEqual(history[2].role, "user")
        result = history[2].parts[0].function_response
        self.assertEqual(result.response, {"result": 100})
        self.assertEqual(result.id, "test-call")

    def test_division_by_zero(self):
        client = mock_client(
            tool_response("divide", 10, 0),
            text_response("Division by zero is not allowed."),
        )
        self.assertIn("zero", self.run_quietly(client))
        result = client.models.generate_content.call_args.kwargs["contents"][2]
        self.assertEqual(result.parts[0].function_response.response,
                         {"error": "Division by zero is not allowed."})

    def test_operations(self):
        for operation, expected in [
            ("add", 14), ("subtract", 6), ("multiply", 40), ("divide", 2.5)
        ]:
            with self.subTest(operation=operation):
                self.assertEqual(calculator(operation, 10, 4), {"result": expected})

    def test_invalid_numbers(self):
        for value in [True, False, None, "4", float("nan"), float("inf"), 10**10000]:
            with self.subTest(value_type=type(value).__name__):
                self.assertIn("error", calculator("add", value, 1))

    def test_invalid_operations_and_overflow(self):
        for arguments in [
            ("eval", 1, 2), ([], 1, 2),
            ("multiply", 1e308, 1e308), ("divide", 1, -0.0),
        ]:
            with self.subTest(arguments=arguments):
                self.assertIn("error", calculator(*arguments))

    def test_invalid_calls(self):
        for name, arguments in [
            ("unknown", {}), ("calculator", None),
            ("calculator", {"operation": "add"}),
            ("calculator", {"expression": "1+2"}),
            ("calculator", {"operation": "add", "a": 1, "b": 2, "extra": 3}),
        ]:
            with self.subTest(name=name, arguments=arguments):
                call = types.FunctionCall(name=name, args=arguments)
                self.assertIn("error", main.execute_tool(call))

    def test_multiple_calls(self):
        first = tool_response("add", 1, 2, "a")
        first.candidates[0].content.parts.extend(
            tool_response("multiply", 3, 4, "b").candidates[0].content.parts
        )
        client = mock_client(first, text_response("3 and 12"))
        self.run_quietly(client)
        parts = client.models.generate_content.call_args.kwargs["contents"][2].parts
        self.assertEqual([p.function_response.response for p in parts],
                         [{"result": 3}, {"result": 12}])
        self.assertEqual([p.function_response.id for p in parts], ["a", "b"])

    def test_empty_prompt(self):
        with self.assertRaises(ValueError):
            self.run_quietly(Mock(), " ")

    def test_empty_response(self):
        for response in [types.GenerateContentResponse(), text_response("")]:
            with self.subTest(response=response), self.assertRaises(RuntimeError):
                self.run_quietly(mock_client(response))

    def test_limit(self):
        client = mock_client(*(tool_response() for _ in range(5)))
        with self.assertRaises(RuntimeError):
            self.run_quietly(client)
        self.assertEqual(client.models.generate_content.call_count, 5)

    def test_missing_key(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(main, "load_dotenv"),
            patch.object(sys, "argv", ["main.py", "--prompt", "Hello"]),
            patch.object(main.genai, "Client") as factory,
            contextlib.redirect_stderr(io.StringIO()) as output,
        ):
            self.assertEqual(main.main(), 1)
            factory.assert_not_called()
            self.assertIn("GEMINI_API_KEY", output.getvalue())

    def test_provider(self):
        with (
            patch.dict(os.environ, {"LLM_PROVIDER": "other"}, clear=True),
            patch.object(main, "load_dotenv"),
            patch.object(sys, "argv", ["main.py"]),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(main.main(), 1)

    def test_api_error_redaction(self):
        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "test-only-not-a-real-key"}, clear=True),
            patch.object(main, "load_dotenv"),
            patch.object(sys, "argv", ["main.py", "--prompt", "Hello"]),
            patch.object(main.genai, "Client", side_effect=Exception("sensitive request")),
            contextlib.redirect_stderr(io.StringIO()) as output,
        ):
            self.assertEqual(main.main(), 1)
            self.assertNotIn("sensitive request", output.getvalue())
            self.assertNotIn("test-only-not-a-real-key", output.getvalue())


def demonstrate_mocked_flow():
    """Exercise the real CLI entry point with simulated Gemini responses."""
    print("\nCLI DEMOS WITH MOCKED SDK RESPONSES (not live Gemini)")
    demos = [
        ("What is the capital of France?", [text_response("Paris is the capital of France.")]),
        ("Use the calculator to multiply 25 by 4.",
         [tool_response(), text_response("25 multiplied by 4 is 100.")]),
        ("Use the calculator to divide 10 by 0.",
         [tool_response("divide", 10, 0), text_response("Division by zero is not allowed.")]),
    ]
    for prompt, responses in demos:
        manager = MagicMock()
        manager.__enter__.return_value = mock_client(*responses)
        print(f"\nYou: {prompt}")
        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "test-only-not-a-real-key"}, clear=True),
            patch.object(main, "load_dotenv"),
            patch.object(sys, "argv", ["main.py", "--prompt", prompt]),
            patch.object(main.genai, "Client", return_value=manager),
        ):
            if main.main() != 0:
                raise RuntimeError("Mocked CLI demonstration failed.")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AgentTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    demonstrate_mocked_flow()
