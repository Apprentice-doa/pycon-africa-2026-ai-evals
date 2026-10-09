# Evaluating Production AI Agents with Logs, Traces, & Evals

**PyCon Africa 2026 Workshop**

A hands-on workshop showing how to fix a broken AI agent using observability and evaluation pipelines.

---

## The Story

**AskBot** is a travel visa assistant for East African travellers.

When a user asks: *"Do I need a visa to go from Kenya to Rwanda?"*

- **v1** answers wrong, cites no source, says "check with the embassy" — useless
- **v2** answers correctly, cites EAC policy, includes source URL — helpful

This workshop shows you how to catch these failures and fix them.

---

## Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd Pycon-Africa-2026-Monitoring-&-Monitoring
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Set your Gemini API key
export GEMINI_API_KEY="your-key-here"

# 3. Run the demo
python demo.py
```

Get a free API key at: https://aistudio.google.com/apikey

---

## Try It Yourself

### Run the agents

```bash
# v1: No observability, bad answers
python -m askbot.v1.agent "Do I need a visa from Kenya to Rwanda?"

# v2: Full tracing, good answers
python -m askbot.v2.agent "Do I need a visa from Kenya to Rwanda?"
```

### Run the evaluations

```bash
# Rule-based checks (free, instant)
python -m evals.rule_based

# LLM-as-Judge (catches factual errors)
python -m evals.llm_judge

# Full pipeline (all three layers)
python -m evals.pipeline
```

---

## What You'll Learn

### 1. Observability

Without it:
```
User: "Why did the bot say I need a visa?"
Engineer: "No idea. We log nothing."
```

With it:
```
trace_id: d20b7230
prompt_version: v2
latency: 1447ms
```

### 2. Three-Layer Evaluation

| Layer | What It Catches | Cost | Speed |
|-------|-----------------|------|-------|
| Rule-based | Missing sources, cop-outs | Free | <1ms |
| LLM Judge | Factual errors, hallucinations | ~$0.001 | 1-2s |
| Human Feedback | Tone, cultural context | Time | Hours |

### 3. Results

```
v1 average score: 0.25
v2 average score: 1.00
Improvement: +0.75
```

---

## Project Structure

```
├── askbot/
│   ├── v1/agent.py      # Broken agent
│   └── v2/agent.py      # Fixed agent with observability
├── evals/
│   ├── rule_based.py    # Fast checks (URLs, cop-outs)
│   ├── llm_judge.py     # Semantic evaluation
│   └── pipeline.py      # Run all layers
├── observability/
│   ├── logging.py       # structlog setup
│   └── tracing.py       # Trace spans
├── prompts/
│   ├── agent_system_v1.txt
│   └── agent_system_v2.txt
└── demo.py              # Interactive workshop
```

---

## Key Files to Explore

1. **`prompts/agent_system_v1.txt`** vs **`agent_system_v2.txt`** — See the prompt fix
2. **`evals/rule_based.py`** — Simple checks that catch obvious failures
3. **`evals/llm_judge.py`** — Using an LLM to evaluate another LLM
4. **`observability/tracing.py`** — How to add trace_id to every request

---

## Resources

- [structlog docs](https://www.structlog.org/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Google AI Studio](https://aistudio.google.com/)

---

## License

MIT — use however you want.
