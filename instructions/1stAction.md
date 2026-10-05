Approved. Please proceed with the implementation step by step according to the final plan.

# Software Quality:
1. Follow the current official python pakcages(e.g. google-genai) function-calling pattern.
2. separation of CLI and agent logic
   
# Validation:
1. Have strong tool validation (e.g. check the arguments must be exactly what the tool expectes)

# Cost Control:
1. have an agent-loop limit(by default: 5)

Important:

* Do not skip the testing step.
* After each major step, briefly explain what you changed and why.
* Do not expose or create any real API key.
* Do not modify files outside `/Volumes/DEV/LAB/ai-agent-lab/agent-project/`.
* If you encounter an error, stop and explain the error rather than making unrelated changes.

After implementation, run the agent and demonstrate at least these test cases:

1. A normal question that does not require the calculator.
2. A multiplication calculation that triggers the calculator tool.
3. A division-by-zero case that demonstrates tool error handling.

Do not add any additional frameworks or features yet.
