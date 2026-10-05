We are starting an AI Agent learning project.

Create a minimal Python project in the current workspace.

Requirements:

1. Create a Python virtual environment.
2. Create a clean project structure.
3. Create a main.py that implements a very simple AI agent.
4. Use an LLM API through an environment variable for the API key.
5. Do NOT use LangChain, LangGraph, or any other agent framework.
6. Create a .env.example file, but never create or expose a real API key.
7. Create a requirements.txt.
8. Create a README.md explaining how the project works.
9. Add basic error handling.
10. Add a simple calculator tool that the agent can call when appropriate.

Architecture Requirements:

11. Do NOT assume OpenAI as the only LLM provider.
    The application architecture must separate the agent logic from the LLM provider.

12. For the first implementation, use Google Gemini API.
    Use GEMINI_API_KEY as the environment variable.

13. Design the code so that the LLM provider can be changed later without rewriting the agent logic.
    For example:
    LLM_PROVIDER=gemini

14. Do NOT use keyword-based or rule-based detection to decide whether to use the calculator.

15. Implement a real LLM tool-calling flow:
    User → LLM → tool call → calculator tool → tool result → LLM → final response.

16. The calculator should be exposed to the LLM as a proper tool with a clear schema.

17. Keep the project simple and educational.
    Do not introduce LangChain, LangGraph, MCP, or other agent frameworks yet.

18. Keep the current simple project structure:
    main.py
    calculator.py
    requirements.txt
    .env.example
    README.md

19. Add .gitignore and make sure .env can never be committed.

20. Before implementing anything, show me the revised architecture and explain the complete tool-calling flow.

Do not modify any files yet.

Final Changes (from user):

21. Use the current official Google Gemini Python SDK:
    `google-genai`
    
    Do NOT use the legacy `google-generativeai` package.

22. Change the calculator tool.
    
    Do NOT accept or evaluate arbitrary mathematical expressions such as:
    `calculator(expression="25 * 4 + 100 / 4")`
    
    Instead expose a safe structured tool such as:
    
    calculator(
        operation: "add" | "subtract" | "multiply" | "divide",
        a: number,
        b: number
    )
    
    The Python implementation must validate the operation and explicitly handle division by zero.

23. Keep the first implementation intentionally simple.
    
    Do not create a complex provider abstraction, factory pattern, dependency injection system, or multiple provider modules yet.
    
    The first version should focus on understanding:
    
    User
    → LLM
    → Tool Call
    → Tool Execution
    → Tool Result
    → LLM
    → Final Answer

24. For this first version, use Gemini directly with the `google-genai` SDK.

25. Keep the project structure simple:
    
    main.py
    calculator.py
    requirements.txt
    .env.example
    .gitignore
    README.md

26. Keep LLM_PROVIDER in the .env.example if useful for future expansion, but do not implement multiple providers yet.

27. Before implementation, show me the final file structure and briefly explain the changes above.

Then wait for my approval.