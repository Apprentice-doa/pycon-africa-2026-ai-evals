#!/usr/bin/env python3
"""
Interactive demo for PyCon Africa workshop.

Run this to walk through the full story:
1. See v1 fail (no observability, wrong answers)
2. See the trace that reveals why
3. See v2 succeed (with observability, correct answers)
4. Run evals to quantify the improvement
"""

import json
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

console = Console()

# Sample data for demo (works without API key)
DEMO_TRACES = json.loads((Path(__file__).parent / "data" / "sample_traces.json").read_text())


def print_header(text: str):
    console.print(f"\n[bold cyan]{'='*60}[/]")
    console.print(f"[bold cyan]{text}[/]")
    console.print(f"[bold cyan]{'='*60}[/]\n")


def demo_v1_failure():
    """Show how v1 fails with no visibility."""
    print_header("PART 1: The Problem — AskBot v1 Fails")
    
    trace = DEMO_TRACES[0]  # v1 trace
    
    console.print("[bold]User asks:[/]")
    console.print(f'  "{trace["question"]}"')
    
    console.print("\n[bold]AskBot v1 responds:[/]")
    console.print(Panel(trace["response"], border_style="red"))
    
    console.print("\n[bold red]User feedback:[/]")
    console.print(f'  👎 "{trace["feedback"]["comment"]}"')
    
    console.print("\n[bold yellow]The engineering team's view:[/]")
    console.print("  • No trace_id")
    console.print("  • No prompt version")
    console.print("  • No tool call logs")
    console.print("  • No idea why it failed")
    
    input("\n[Press Enter to continue...]")


def demo_trace_analysis():
    """Show how traces reveal the problem."""
    print_header("PART 2: Adding Observability — Now We Can See")
    
    trace = DEMO_TRACES[0]
    
    console.print("[bold]With tracing enabled, we can see the waterfall:[/]\n")
    
    # Show trace structure
    trace_json = json.dumps(trace["spans"], indent=2)
    console.print(Syntax(trace_json, "json", theme="monokai"))
    
    console.print("\n[bold yellow]What the trace reveals:[/]")
    console.print("  1. Agent ran a web search for 'Kenya Rwanda visa requirements'")
    console.print("  2. Top result was from 2019 (pre-EAC expansion)")
    console.print("  3. Agent trusted outdated information")
    console.print("  4. No EAC-specific check was performed")
    
    input("\n[Press Enter to continue...]")


def demo_v2_success():
    """Show how v2 succeeds with better prompt + observability."""
    print_header("PART 3: The Fix — AskBot v2 with Better Prompt")
    
    trace = DEMO_TRACES[1]  # v2 trace
    
    console.print("[bold]Same question:[/]")
    console.print(f'  "{trace["question"]}"')
    
    console.print("\n[bold]AskBot v2 responds:[/]")
    console.print(Panel(trace["response"], border_style="green"))
    
    console.print("\n[bold green]User feedback:[/]")
    console.print(f'  👍 "{trace["feedback"]["comment"]}"')
    
    console.print("\n[bold]What changed in the prompt (agent_system_v2.txt):[/]")
    console.print("  1. EAC First: Always check EAC status before anything else")
    console.print("  2. Always Cite Sources: Every answer must have a URL")
    console.print("  3. No Cop-outs: Never say 'check embassy' without a link")
    
    input("\n[Press Enter to continue...]")


def demo_eval_pipeline():
    """Show the three-layer eval pipeline."""
    print_header("PART 4: Evaluation Pipeline — Quantifying Quality")
    
    console.print("[bold]Three-layer evaluation:[/]\n")
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Layer")
    table.add_column("What It Catches")
    table.add_column("Cost")
    table.add_column("Speed")
    
    table.add_row(
        "1. Rule-based",
        "Missing sources, format issues, cop-outs",
        "Free",
        "< 1ms"
    )
    table.add_row(
        "2. LLM-as-Judge",
        "Factual errors, grounding failures",
        "~$0.001/eval",
        "~1-2s"
    )
    table.add_row(
        "3. Human Feedback",
        "Tone issues, cultural context",
        "Time",
        "Hours/days"
    )
    
    console.print(table)
    
    console.print("\n[bold]Running evals on v1 vs v2...[/]\n")
    
    # Simulated results
    results_table = Table(show_header=True, header_style="bold")
    results_table.add_column("Metric")
    results_table.add_column("v1", style="red")
    results_table.add_column("v2", style="green")
    
    results_table.add_row("Rule-based score", "0.25", "1.00")
    results_table.add_row("LLM Judge score", "0.30", "0.95")
    results_table.add_row("Human thumbs-up rate", "13%", "94%")
    results_table.add_row("[bold]Overall score[/]", "[bold]0.26[/]", "[bold]0.91[/]")
    
    console.print(results_table)
    
    console.print("\n[bold green]Result: Score improved from 0.26 → 0.91[/]")
    console.print("[bold green]Thumbs-down rate dropped from 87% → 6%[/]")


def demo_live_agent():
    """Run the actual agents (requires API key)."""
    print_header("PART 5: Live Demo — Try It Yourself")
    
    import os
    if not os.environ.get("GEMINI_API_KEY"):
        console.print("[yellow]Set GEMINI_API_KEY to run live demo[/]")
        console.print("\nTo run manually:")
        console.print("  python -m askbot.v1.agent 'Do I need a visa from Kenya to Rwanda?'")
        console.print("  python -m askbot.v2.agent 'Do I need a visa from Kenya to Rwanda?'")
        return
    
    question = console.input("\n[bold]Enter a visa question (or press Enter for default):[/] ")
    if not question:
        question = "Do I need a visa to go from Kenya to Rwanda?"
    
    console.print(f"\n[bold]Question:[/] {question}")
    
    # Run v1
    console.print("\n[bold red]Running v1 (no observability)...[/]")
    from askbot.v1 import ask as ask_v1
    v1_response = ask_v1(question)
    console.print(Panel(v1_response, title="v1 Response", border_style="red"))
    
    # Run v2
    console.print("\n[bold green]Running v2 (with observability)...[/]")
    from askbot.v2 import ask as ask_v2
    v2_result = ask_v2(question)
    console.print(Panel(v2_result.answer, title="v2 Response", border_style="green"))
    console.print(f"  trace_id: {v2_result.trace_id}")
    console.print(f"  prompt_version: {v2_result.prompt_version}")
    console.print(f"  latency: {v2_result.latency_ms:.0f}ms")


def main():
    console.print(Panel.fit(
        "[bold]Evaluating Production AI Agents\nwith Logs, Traces, & Evals[/]\n\n"
        "PyCon Africa 2026 Workshop",
        border_style="cyan"
    ))
    
    console.print("\nThis demo walks through:")
    console.print("  1. How AskBot v1 fails (and why we can't debug it)")
    console.print("  2. How traces reveal the root cause")
    console.print("  3. How v2 fixes it with a better prompt")
    console.print("  4. How to quantify improvement with evals")
    console.print("  5. Live demo (if API key is set)")
    
    input("\n[Press Enter to start...]")
    
    demo_v1_failure()
    demo_trace_analysis()
    demo_v2_success()
    demo_eval_pipeline()
    demo_live_agent()
    
    print_header("Workshop Complete!")
    console.print("Key takeaways:")
    console.print("  1. [bold]Observability first[/] — you can't fix what you can't see")
    console.print("  2. [bold]Layer your evals[/] — rules + LLM + human feedback")
    console.print("  3. [bold]Iterate on prompts[/] — small changes, big impact")
    console.print("\nResources:")
    console.print("  • structlog: https://www.structlog.org/")
    console.print("  • OpenTelemetry: https://opentelemetry.io/")
    console.print("  • This repo: github.com/your-handle/askbot-evals")


if __name__ == "__main__":
    main()
