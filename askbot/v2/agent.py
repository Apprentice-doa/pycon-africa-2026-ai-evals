"""
AskBot v2 — The fixed agent.

Improvements:
- Full observability (trace_id, prompt_version, tool call logs)
- Better system prompt (EAC-aware, requires sources, no cop-outs)
- Structured response format
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass

from google import genai

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from observability import setup_logging, get_logger, bind_context, clear_context
from observability import get_tracer

# Load the (good) v2 prompt
PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "agent_system_v2.txt"
SYSTEM_PROMPT = PROMPT_PATH.read_text()
PROMPT_VERSION = "v2"


@dataclass
class AgentResponse:
    """Structured response with metadata for debugging."""
    answer: str
    trace_id: str
    prompt_version: str
    model: str
    latency_ms: float


def ask(question: str, json_logs: bool = False) -> AgentResponse:
    """
    Ask the v2 agent a question.
    
    Returns structured response with full observability metadata.
    """
    setup_logging(json_output=json_logs)
    log = get_logger("askbot.v2")
    tracer = get_tracer()
    
    # Start trace and bind context
    trace_id = tracer.start_trace("ask_question")
    bind_context(trace_id=trace_id, prompt_version=PROMPT_VERSION)
    
    log.info("request_started", question=question)
    tracer.set_attribute("question", question)
    tracer.set_attribute("prompt_version", PROMPT_VERSION)
    
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # LLM call with tracing
    with tracer.span("llm_call", {"model": "gemini-3.5-flash-lite"}) as span:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=f"{SYSTEM_PROMPT}\n\nUser: {question}",
        )
    
    answer = response.text
    latency_ms = tracer.get_trace()[-1]["duration_ms"] or 0
    
    log.info("request_completed", latency_ms=latency_ms)
    
    tracer.end_span()  # End root span
    clear_context()
    
    return AgentResponse(
        answer=answer,
        trace_id=trace_id,
        prompt_version=PROMPT_VERSION,
        model="gemini-3.5-flash-lite",
        latency_ms=latency_ms,
    )


def main():
    import sys
    
    if len(sys.argv) < 2:
        question = "Do I need a visa to go from Kenya to Rwanda?"
    else:
        question = " ".join(sys.argv[1:])
    
    print(f"Question: {question}\n")
    
    result = ask(question, json_logs=False)
    
    print(f"\nAnswer: {result.answer}")
    print(f"\n--- Metadata ---")
    print(f"trace_id: {result.trace_id}")
    print(f"prompt_version: {result.prompt_version}")
    print(f"model: {result.model}")
    print(f"latency: {result.latency_ms:.0f}ms")


if __name__ == "__main__":
    main()
