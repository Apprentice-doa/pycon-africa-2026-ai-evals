"""
AskBot v1 — The broken agent.

Problems:
- No observability (no trace_id, no prompt version tracking)
- Bad system prompt (no EAC awareness, allows cop-out answers)
- No source citation requirement
"""

import os
from pathlib import Path
from google import genai

# Load the (bad) v1 prompt
PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "agent_system_v1.txt"
SYSTEM_PROMPT = PROMPT_PATH.read_text()


def ask(question: str) -> str:
    """
    Ask the v1 agent a question.
    
    Note: No logging, no tracing, no context. 
    When this fails in prod, you'll have no idea why.
    """
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=f"{SYSTEM_PROMPT}\n\nUser: {question}",
    )
    
    return response.text


def main():
    import sys
    
    if len(sys.argv) < 2:
        question = "Do I need a visa to go from Kenya to Rwanda?"
    else:
        question = " ".join(sys.argv[1:])
    
    print(f"Question: {question}\n")
    print(f"Answer: {ask(question)}")


if __name__ == "__main__":
    main()
