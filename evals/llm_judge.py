"""
LLM-as-Judge evaluation — catches semantic failures that rules miss.

Use this to check:
- Factual accuracy (is the answer correct?)
- Grounding (is it based on retrieved context, not hallucinated?)
- Relevance (does it actually answer the question?)
"""

import json
import os
from dataclasses import dataclass
from typing import Optional
from google import genai


@dataclass
class JudgeResult:
    factual_accuracy: float  # 0-1: Is the information correct?
    grounding: float         # 0-1: Is it based on real sources?
    relevance: float         # 0-1: Does it answer the question?
    reasoning: str           # Why the judge gave these scores
    
    @property
    def overall_score(self) -> float:
        """Weighted average. Factual accuracy matters most."""
        return (
            self.factual_accuracy * 0.5 +
            self.grounding * 0.3 +
            self.relevance * 0.2
        )


JUDGE_PROMPT = """You are evaluating an AI assistant's response about visa requirements for East African travellers.

CONTEXT:
- The East African Community (EAC) includes: Kenya, Uganda, Tanzania, Rwanda, Burundi, South Sudan, and DRC
- EAC citizens can travel freely within the bloc using national ID (no visa required)
- This is a well-established policy, not new or uncertain

QUESTION: {question}

RESPONSE TO EVALUATE:
{response}

GROUND TRUTH (if available): {ground_truth}

Score the response on three dimensions (0.0 to 1.0):

1. factual_accuracy: Is the information correct? 
   - 1.0 = Completely correct
   - 0.5 = Partially correct or missing key info
   - 0.0 = Wrong

2. grounding: Is the response grounded in real, verifiable information?
   - 1.0 = Cites real sources, information is verifiable
   - 0.5 = No sources but information seems accurate
   - 0.0 = Appears hallucinated or made up

3. relevance: Does it actually answer the user's question?
   - 1.0 = Directly answers the question
   - 0.5 = Partially answers or is vague
   - 0.0 = Doesn't answer the question

Respond ONLY with valid JSON (no markdown, no extra text):
{{"factual_accuracy": <float>, "grounding": <float>, "relevance": <float>, "reasoning": "<brief explanation>"}}"""


class LLMJudge:
    """Use an LLM to evaluate response quality."""
    
    def __init__(self, model_name: str = "gemini-3.5-flash-lite"):
        self.model_name = model_name
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    def evaluate(
        self, 
        question: str, 
        response: str, 
        ground_truth: Optional[str] = None
    ) -> JudgeResult:
        """
        Have the LLM judge the response quality.
        """
        prompt = JUDGE_PROMPT.format(
            question=question,
            response=response,
            ground_truth=ground_truth or "Not provided"
        )
        
        result = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        
        # Parse JSON from response
        text = result.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        scores = json.loads(text)
        
        return JudgeResult(
            factual_accuracy=float(scores.get("factual_accuracy", 0)),
            grounding=float(scores.get("grounding", 0)),
            relevance=float(scores.get("relevance", 0)),
            reasoning=scores.get("reasoning", ""),
        )


if __name__ == "__main__":
    judge = LLMJudge()
    
    question = "Do I need a visa to go from Kenya to Rwanda?"
    
    ground_truth = """No visa needed. Kenyan citizens can enter Rwanda freely 
    under the EAC free movement protocol using a national ID or passport."""
    
    bad_response = """
    For travel from Kenya to Rwanda, you will likely need a visa. 
    I recommend checking with the Rwandan embassy for the most current 
    requirements as visa policies can change frequently.
    """
    
    good_response = """
    **No visa needed.** As a Kenyan citizen, you can enter Rwanda visa-free 
    under the EAC free movement protocol. You only need a valid Kenyan 
    national ID or passport.
    
    **Source**: https://www.migration.go.ke/eac-free-movement
    """
    
    print("=== Bad Response (v1) ===")
    result = judge.evaluate(question, bad_response, ground_truth)
    print(f"  Factual accuracy: {result.factual_accuracy:.2f}")
    print(f"  Grounding: {result.grounding:.2f}")
    print(f"  Relevance: {result.relevance:.2f}")
    print(f"  Overall: {result.overall_score:.2f}")
    print(f"  Reasoning: {result.reasoning}")
    
    print("\n=== Good Response (v2) ===")
    result = judge.evaluate(question, good_response, ground_truth)
    print(f"  Factual accuracy: {result.factual_accuracy:.2f}")
    print(f"  Grounding: {result.grounding:.2f}")
    print(f"  Relevance: {result.relevance:.2f}")
    print(f"  Overall: {result.overall_score:.2f}")
    print(f"  Reasoning: {result.reasoning}")
