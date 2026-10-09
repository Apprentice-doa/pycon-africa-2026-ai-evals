"""
OpenTelemetry tracing setup for AskBot.

Traces show you the full request waterfall:
- How long did the LLM call take?
- What tools were called and in what order?
- Where did the request spend most of its time?
"""

import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List


@dataclass
class Span:
    """A single unit of work in a trace."""
    name: str
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "OK"
    
    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status,
        }


class Tracer:
    """
    Lightweight tracer for demo purposes.
    
    In production, use opentelemetry-sdk with an exporter (Jaeger, Zipkin, etc.)
    This implementation captures the same concepts without external dependencies.
    """
    
    def __init__(self):
        self._spans: List[Span] = []
        self._current_span: Optional[Span] = None
        self._trace_id: Optional[str] = None
    
    def start_trace(self, name: str = "request") -> str:
        """Start a new trace. Returns the trace_id."""
        self._trace_id = str(uuid.uuid4())[:8]
        self._spans = []
        self._current_span = None
        self.start_span(name)
        return self._trace_id
    
    @contextmanager
    def span(self, name: str, attributes: Dict[str, Any] = None):
        """Context manager for creating spans."""
        span = self.start_span(name, attributes)
        try:
            yield span
        except Exception as e:
            span.status = "ERROR"
            span.events.append({
                "name": "exception",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "attributes": {"exception.message": str(e)}
            })
            raise
        finally:
            self.end_span()
    
    def start_span(self, name: str, attributes: Dict[str, Any] = None) -> Span:
        """Start a new span."""
        span = Span(
            name=name,
            trace_id=self._trace_id or str(uuid.uuid4())[:8],
            span_id=str(uuid.uuid4())[:8],
            parent_id=self._current_span.span_id if self._current_span else None,
            start_time=datetime.now(timezone.utc),
            attributes=attributes or {},
        )
        self._spans.append(span)
        self._current_span = span
        return span
    
    def end_span(self):
        """End the current span."""
        if self._current_span:
            self._current_span.end_time = datetime.now(timezone.utc)
            # Find parent span
            if self._current_span.parent_id:
                for span in self._spans:
                    if span.span_id == self._current_span.parent_id:
                        self._current_span = span
                        return
            self._current_span = None
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        """Add an event to the current span."""
        if self._current_span:
            self._current_span.events.append({
                "name": name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "attributes": attributes or {},
            })
    
    def set_attribute(self, key: str, value: Any):
        """Set an attribute on the current span."""
        if self._current_span:
            self._current_span.attributes[key] = value
    
    def get_trace(self) -> List[dict]:
        """Get all spans in the current trace."""
        return [span.to_dict() for span in self._spans]
    
    @property
    def trace_id(self) -> Optional[str]:
        return self._trace_id


# Global tracer instance
_tracer = Tracer()

def get_tracer() -> Tracer:
    return _tracer


if __name__ == "__main__":
    import json
    
    # Demo
    tracer = get_tracer()
    trace_id = tracer.start_trace("ask_question")
    
    tracer.set_attribute("question", "Do I need a visa from Kenya to Rwanda?")
    tracer.set_attribute("prompt_version", "v1")
    
    with tracer.span("web_search", {"query": "Kenya Rwanda visa requirements"}):
        tracer.add_event("search_results", {"count": 5})
    
    with tracer.span("llm_call", {"model": "gpt-4"}):
        tracer.set_attribute("prompt_tokens", 150)
        tracer.set_attribute("completion_tokens", 89)
    
    tracer.end_span()  # End root span
    
    print(json.dumps(tracer.get_trace(), indent=2))
