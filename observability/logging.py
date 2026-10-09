"""
Structured logging setup for AskBot.

Why structlog?
- JSON output (machine-readable, queryable)
- Automatic context binding (trace_id follows the request)
- UTC timestamps (no timezone confusion in prod)
"""

import structlog
import logging
import sys
from datetime import datetime, timezone


def setup_logging(json_output: bool = True, level: str = "INFO"):
    """
    Configure structlog for production use.
    
    Args:
        json_output: True for JSON (prod), False for pretty console (dev)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    
    # Shared processors for all output formats
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.ExtraAdder(),
    ]
    
    if json_output:
        # Production: JSON lines
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    else:
        # Development: colored console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """Get a logger instance with optional name binding."""
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(component=name)
    return logger


# Convenience: bind request context that follows all subsequent logs
bind_context = structlog.contextvars.bind_contextvars
clear_context = structlog.contextvars.clear_contextvars


if __name__ == "__main__":
    # Demo
    setup_logging(json_output=False)
    log = get_logger("demo")
    
    bind_context(trace_id="abc-123", user_id="user-456")
    
    log.info("request_started", endpoint="/ask")
    log.info("llm_call", model="gpt-4", prompt_tokens=150)
    log.info("request_completed", latency_ms=1240)
