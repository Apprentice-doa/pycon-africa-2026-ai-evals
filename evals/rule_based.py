"""
Rule-based evaluation — fast, cheap, catches obvious failures.

These run in milliseconds and cost nothing. Use them to catch:
- Missing source URLs
- Response too long/short
- Cop-out phrases
- Format violations
"""

import re
from dataclasses import dataclass
from typing import List, Callable


@dataclass
class RuleResult:
    name: str
    passed: bool
    message: str


class RuleBasedEval:
    """Collection of rule-based checks for agent responses."""
    
    def __init__(self):
        self.rules: List[Callable[[str, str], RuleResult]] = [
            self._has_source_url,
            self._no_embassy_copout,
            self._reasonable_length,
            self._no_uncertainty_hedging,
        ]
    
    def evaluate(self, question: str, response: str) -> List[RuleResult]:
        """Run all rules against a response."""
        return [rule(question, response) for rule in self.rules]
    
    def score(self, question: str, response: str) -> float:
        """Return pass rate as a score between 0 and 1."""
        results = self.evaluate(question, response)
        passed = sum(1 for r in results if r.passed)
        return passed / len(results) if results else 0.0
    
    def _has_source_url(self, question: str, response: str) -> RuleResult:
        """Response must contain at least one URL."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        has_url = bool(re.search(url_pattern, response))
        return RuleResult(
            name="has_source_url",
            passed=has_url,
            message="Response contains source URL" if has_url else "Missing source URL"
        )
    
    def _no_embassy_copout(self, question: str, response: str) -> RuleResult:
        """
        If response mentions "embassy", it must include a URL.
        Saying "check with the embassy" without a link is useless.
        """
        response_lower = response.lower()
        mentions_embassy = "embassy" in response_lower
        
        if not mentions_embassy:
            return RuleResult(
                name="no_embassy_copout",
                passed=True,
                message="No embassy mention (good)"
            )
        
        # If embassy is mentioned, there must be a URL nearby
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        has_url = bool(re.search(url_pattern, response))
        
        return RuleResult(
            name="no_embassy_copout",
            passed=has_url,
            message="Embassy mentioned with URL" if has_url else "Embassy cop-out without URL"
        )
    
    def _reasonable_length(self, question: str, response: str) -> RuleResult:
        """Response should be between 50 and 1000 characters."""
        length = len(response)
        passed = 50 <= length <= 1000
        
        if length < 50:
            msg = f"Response too short ({length} chars)"
        elif length > 1000:
            msg = f"Response too long ({length} chars)"
        else:
            msg = f"Response length OK ({length} chars)"
        
        return RuleResult(name="reasonable_length", passed=passed, message=msg)
    
    def _no_uncertainty_hedging(self, question: str, response: str) -> RuleResult:
        """
        Avoid excessive hedging phrases that make the response useless.
        Some hedging is fine, but not as the main answer.
        """
        hedge_phrases = [
            "i'm not sure",
            "i don't know",
            "i cannot provide",
            "i'm unable to",
            "you should verify",
            "please confirm",
            "requirements may vary",
            "subject to change",
        ]
        
        response_lower = response.lower()
        found_hedges = [p for p in hedge_phrases if p in response_lower]
        
        # Allow up to 1 hedge phrase
        passed = len(found_hedges) <= 1
        
        if not found_hedges:
            msg = "No hedging phrases"
        elif passed:
            msg = f"Minor hedging: {found_hedges[0]}"
        else:
            msg = f"Excessive hedging: {', '.join(found_hedges)}"
        
        return RuleResult(name="no_uncertainty_hedging", passed=passed, message=msg)


if __name__ == "__main__":
    # Demo
    evaluator = RuleBasedEval()
    
    # Bad response (v1 style)
    bad_response = """
    For travel from Kenya to Rwanda, you may need a visa depending on your 
    citizenship status. I recommend checking with the Rwandan embassy for 
    the most up-to-date requirements as these can change. Requirements may 
    vary based on your specific situation.
    """
    
    # Good response (v2 style)
    good_response = """
    **No visa needed.** As a Kenyan citizen, you can enter Rwanda visa-free 
    under the EAC free movement protocol. You only need a valid Kenyan 
    national ID or passport.
    
    **Source**: https://www.migration.go.ke/eac-free-movement
    """
    
    question = "Do I need a visa to go from Kenya to Rwanda?"
    
    print("=== Bad Response (v1) ===")
    for result in evaluator.evaluate(question, bad_response):
        status = "✓" if result.passed else "✗"
        print(f"  {status} {result.name}: {result.message}")
    print(f"  Score: {evaluator.score(question, bad_response):.2f}")
    
    print("\n=== Good Response (v2) ===")
    for result in evaluator.evaluate(question, good_response):
        status = "✓" if result.passed else "✗"
        print(f"  {status} {result.name}: {result.message}")
    print(f"  Score: {evaluator.score(question, good_response):.2f}")
