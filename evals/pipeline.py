"""
Three-layer evaluation pipeline.

Layer 1: Rule-based (fast, free)
Layer 2: LLM-as-Judge (slower, costs money, catches semantic issues)
Layer 3: Human feedback (slowest, most valuable for edge cases)

Run all layers and aggregate into a single score.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from .rule_based import RuleBasedEval, RuleResult
from .llm_judge import LLMJudge, JudgeResult


@dataclass
class HumanFeedback:
    """Human feedback on a response."""
    thumbs_up: bool
    comment: Optional[str] = None
    
    @property
    def score(self) -> float:
        return 1.0 if self.thumbs_up else 0.0


@dataclass
class EvalResult:
    """Combined result from all evaluation layers."""
    question: str
    response: str
    
    # Layer 1: Rules
    rule_results: List[RuleResult]
    rule_score: float
    
    # Layer 2: LLM Judge
    judge_result: Optional[JudgeResult]
    judge_score: float
    
    # Layer 3: Human (optional)
    human_feedback: Optional[HumanFeedback]
    human_score: Optional[float]
    
    @property
    def overall_score(self) -> float:
        """
        Weighted combination of all layers.
        
        Weights:
        - Rules: 20% (fast sanity checks)
        - LLM Judge: 50% (semantic quality)
        - Human: 30% (real-world signal)
        
        If human feedback is missing, redistribute weight to LLM judge.
        """
        if self.human_score is not None:
            return (
                self.rule_score * 0.2 +
                self.judge_score * 0.5 +
                self.human_score * 0.3
            )
        else:
            return (
                self.rule_score * 0.25 +
                self.judge_score * 0.75
            )
    
    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "response": self.response,
            "rule_score": self.rule_score,
            "judge_score": self.judge_score,
            "human_score": self.human_score,
            "overall_score": self.overall_score,
            "rule_details": [asdict(r) for r in self.rule_results],
            "judge_reasoning": self.judge_result.reasoning if self.judge_result else None,
        }


class EvalPipeline:
    """Run the full three-layer evaluation pipeline."""
    
    def __init__(self, use_llm_judge: bool = True):
        self.rule_eval = RuleBasedEval()
        self.llm_judge = LLMJudge() if use_llm_judge else None
    
    def evaluate(
        self,
        question: str,
        response: str,
        ground_truth: Optional[str] = None,
        human_feedback: Optional[HumanFeedback] = None,
    ) -> EvalResult:
        """
        Run all evaluation layers on a response.
        
        Args:
            question: The user's question
            response: The agent's response
            ground_truth: Optional correct answer for LLM judge
            human_feedback: Optional human feedback (thumbs up/down)
        """
        # Layer 1: Rule-based
        rule_results = self.rule_eval.evaluate(question, response)
        rule_score = self.rule_eval.score(question, response)
        
        # Layer 2: LLM Judge
        judge_result = None
        judge_score = 0.0
        if self.llm_judge:
            judge_result = self.llm_judge.evaluate(question, response, ground_truth)
            judge_score = judge_result.overall_score
        
        # Layer 3: Human feedback (passed in, not collected here)
        human_score = human_feedback.score if human_feedback else None
        
        return EvalResult(
            question=question,
            response=response,
            rule_results=rule_results,
            rule_score=rule_score,
            judge_result=judge_result,
            judge_score=judge_score,
            human_feedback=human_feedback,
            human_score=human_score,
        )
    
    def evaluate_batch(
        self,
        test_cases: List[dict],
    ) -> List[EvalResult]:
        """
        Evaluate a batch of test cases.
        
        Each test case should have:
        - question: str
        - response: str
        - ground_truth: str (optional)
        - thumbs_up: bool (optional)
        """
        results = []
        for case in test_cases:
            human_fb = None
            if "thumbs_up" in case:
                human_fb = HumanFeedback(
                    thumbs_up=case["thumbs_up"],
                    comment=case.get("comment")
                )
            
            result = self.evaluate(
                question=case["question"],
                response=case["response"],
                ground_truth=case.get("ground_truth"),
                human_feedback=human_fb,
            )
            results.append(result)
        
        return results


def main():
    """Run eval pipeline on test cases."""
    
    # Load test cases
    test_cases_path = Path(__file__).parent.parent / "data" / "test_cases.json"
    
    if not test_cases_path.exists():
        print(f"No test cases found at {test_cases_path}")
        print("Creating sample test cases...")
        
        # Create sample test cases
        sample_cases = [
            {
                "question": "Do I need a visa to go from Kenya to Rwanda?",
                "response": "For travel from Kenya to Rwanda, you may need a visa. Please check with the Rwandan embassy for current requirements.",
                "ground_truth": "No visa needed. Kenyan citizens can enter Rwanda freely under EAC free movement.",
                "thumbs_up": False,
                "comment": "Wrong answer, no source",
                "version": "v1"
            },
            {
                "question": "Do I need a visa to go from Kenya to Rwanda?",
                "response": "**No visa needed.** As a Kenyan citizen, you can enter Rwanda visa-free under the EAC free movement protocol. You only need a valid Kenyan national ID or passport.\n\n**Source**: https://www.migration.go.ke/eac-free-movement",
                "ground_truth": "No visa needed. Kenyan citizens can enter Rwanda freely under EAC free movement.",
                "thumbs_up": True,
                "comment": "Clear, correct, has source",
                "version": "v2"
            },
            {
                "question": "Can I travel from Uganda to Tanzania with just my national ID?",
                "response": "I'm not sure about the specific requirements. You should verify with the Tanzanian embassy as requirements may vary.",
                "ground_truth": "Yes, EAC citizens can travel within the bloc using national ID.",
                "thumbs_up": False,
                "comment": "Useless non-answer",
                "version": "v1"
            },
            {
                "question": "Can I travel from Uganda to Tanzania with just my national ID?",
                "response": "**Yes.** As a Ugandan citizen, you can enter Tanzania using your national ID under the EAC free movement protocol. No passport required for EAC member state travel.\n\n**Source**: https://www.eac.int/free-movement",
                "ground_truth": "Yes, EAC citizens can travel within the bloc using national ID.",
                "thumbs_up": True,
                "version": "v2"
            },
        ]
        
        test_cases_path.parent.mkdir(parents=True, exist_ok=True)
        test_cases_path.write_text(json.dumps(sample_cases, indent=2))
        print(f"Created {test_cases_path}")
    
    test_cases = json.loads(test_cases_path.read_text())
    
    print("Running evaluation pipeline...\n")
    print("=" * 60)
    
    pipeline = EvalPipeline(use_llm_judge=True)
    
    v1_scores = []
    v2_scores = []
    
    for case in test_cases:
        human_fb = HumanFeedback(
            thumbs_up=case.get("thumbs_up", False),
            comment=case.get("comment")
        ) if "thumbs_up" in case else None
        
        result = pipeline.evaluate(
            question=case["question"],
            response=case["response"],
            ground_truth=case.get("ground_truth"),
            human_feedback=human_fb,
        )
        
        version = case.get("version", "unknown")
        if version == "v1":
            v1_scores.append(result.overall_score)
        else:
            v2_scores.append(result.overall_score)
        
        print(f"Version: {version}")
        print(f"Question: {case['question'][:50]}...")
        print(f"Rule Score: {result.rule_score:.2f}")
        print(f"Judge Score: {result.judge_score:.2f}")
        print(f"Human Score: {result.human_score}")
        print(f"Overall: {result.overall_score:.2f}")
        
        # Show failed rules
        failed = [r for r in result.rule_results if not r.passed]
        if failed:
            print(f"Failed rules: {[r.name for r in failed]}")
        
        if result.judge_result:
            print(f"Judge reasoning: {result.judge_result.reasoning[:100]}...")
        
        print("-" * 60)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if v1_scores:
        print(f"v1 average score: {sum(v1_scores)/len(v1_scores):.2f}")
    if v2_scores:
        print(f"v2 average score: {sum(v2_scores)/len(v2_scores):.2f}")
    
    if v1_scores and v2_scores:
        improvement = (sum(v2_scores)/len(v2_scores)) - (sum(v1_scores)/len(v1_scores))
        print(f"Improvement: +{improvement:.2f}")


if __name__ == "__main__":
    main()
