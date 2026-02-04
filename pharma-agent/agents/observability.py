"""
Agent Observability - Langfuse Integration and Tracing

This module provides:
1. Langfuse SDK integration for production tracing
2. Fallback console logging when no API keys configured
3. Trace logging for all agent decisions and interactions
4. Public trace link generation
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class TraceSpan:
    """Represents a single span in a trace."""
    span_id: str
    parent_id: Optional[str]
    name: str
    agent: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: str = "running"
    started_at: str = ""
    ended_at: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ObservabilityManager:
    """
    Manages observability and tracing for the multi-agent system.
    Uses Langfuse if configured, otherwise falls back to console logging.
    """
    
    def __init__(self):
        self.langfuse_client = None
        self.traces: Dict[str, Dict] = {}
        self.console_mode = True
        
        # Try to initialize Langfuse
        self._init_langfuse()
    
    def _init_langfuse(self):
        """Initialize Langfuse client if configured."""
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        if public_key and secret_key:
            try:
                from langfuse import Langfuse
                self.langfuse_client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host
                )
                self.console_mode = False
                print("✅ Langfuse observability initialized")
            except ImportError:
                print("⚠️ Langfuse package not installed. Using console logging.")
            except Exception as e:
                print(f"⚠️ Langfuse init failed: {e}. Using console logging.")
        else:
            print("ℹ️ Langfuse keys not configured. Using console logging for observability.")
    
    def start_trace(
        self,
        name: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Start a new trace."""
        trace_id = str(uuid.uuid4())
        
        trace_data = {
            "trace_id": trace_id,
            "name": name,
            "session_id": session_id,
            "user_id": user_id,
            "metadata": metadata or {},
            "spans": [],
            "started_at": datetime.utcnow().isoformat(),
            "ended_at": None,
            "status": "running"
        }
        
        self.traces[trace_id] = trace_data
        
        if self.langfuse_client:
            try:
                self.langfuse_client.trace(
                    id=trace_id,
                    name=name,
                    session_id=session_id,
                    user_id=user_id,
                    metadata=metadata
                )
            except Exception as e:
                print(f"Langfuse trace error: {e}")
        
        if self.console_mode:
            self._log_console("TRACE_START", {
                "trace_id": trace_id,
                "name": name,
                "session_id": session_id
            })
        
        return trace_id
    
    def start_span(
        self,
        trace_id: str,
        name: str,
        agent: str,
        input_data: Dict[str, Any],
        parent_span_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Start a new span within a trace."""
        span_id = str(uuid.uuid4())
        
        span = TraceSpan(
            span_id=span_id,
            parent_id=parent_span_id,
            name=name,
            agent=agent,
            input_data=input_data,
            started_at=datetime.utcnow().isoformat(),
            metadata=metadata
        )
        
        if trace_id in self.traces:
            self.traces[trace_id]["spans"].append(asdict(span))
        
        if self.langfuse_client:
            try:
                self.langfuse_client.span(
                    trace_id=trace_id,
                    id=span_id,
                    parent_observation_id=parent_span_id,
                    name=name,
                    input=input_data,
                    metadata={"agent": agent, **(metadata or {})}
                )
            except Exception as e:
                print(f"Langfuse span error: {e}")
        
        if self.console_mode:
            self._log_console("SPAN_START", {
                "trace_id": trace_id,
                "span_id": span_id,
                "agent": agent,
                "name": name,
                "input": self._truncate_data(input_data)
            })
        
        return span_id
    
    def end_span(
        self,
        trace_id: str,
        span_id: str,
        output_data: Dict[str, Any],
        status: str = "completed"
    ):
        """End a span and record output."""
        ended_at = datetime.utcnow().isoformat()
        
        # Update local trace
        if trace_id in self.traces:
            for span in self.traces[trace_id]["spans"]:
                if span["span_id"] == span_id:
                    span["output_data"] = output_data
                    span["status"] = status
                    span["ended_at"] = ended_at
                    # Calculate duration
                    start = datetime.fromisoformat(span["started_at"])
                    end = datetime.fromisoformat(ended_at)
                    span["duration_ms"] = int((end - start).total_seconds() * 1000)
                    break
        
        if self.langfuse_client:
            try:
                # Update span with output
                self.langfuse_client.span(
                    trace_id=trace_id,
                    id=span_id,
                    output=output_data,
                    status_message=status
                )
            except Exception as e:
                print(f"Langfuse span end error: {e}")
        
        if self.console_mode:
            self._log_console("SPAN_END", {
                "trace_id": trace_id,
                "span_id": span_id,
                "status": status,
                "output": self._truncate_data(output_data)
            })
    
    def end_trace(self, trace_id: str, status: str = "completed"):
        """End a trace."""
        if trace_id in self.traces:
            self.traces[trace_id]["ended_at"] = datetime.utcnow().isoformat()
            self.traces[trace_id]["status"] = status
        
        if self.langfuse_client:
            try:
                self.langfuse_client.flush()
            except Exception as e:
                print(f"Langfuse flush error: {e}")
        
        if self.console_mode:
            self._log_console("TRACE_END", {
                "trace_id": trace_id,
                "status": status
            })
    
    def log_decision(
        self,
        trace_id: str,
        agent: str,
        decision: str,
        reason: str,
        data: Optional[Dict] = None
    ):
        """Log an agent decision."""
        decision_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "decision": decision,
            "reason": reason,
            "data": data or {}
        }
        
        if trace_id in self.traces:
            if "decisions" not in self.traces[trace_id]:
                self.traces[trace_id]["decisions"] = []
            self.traces[trace_id]["decisions"].append(decision_log)
        
        if self.langfuse_client:
            try:
                self.langfuse_client.event(
                    trace_id=trace_id,
                    name=f"decision:{decision}",
                    input={"reason": reason, **data} if data else {"reason": reason},
                    metadata={"agent": agent}
                )
            except Exception as e:
                print(f"Langfuse event error: {e}")
        
        if self.console_mode:
            self._log_console("DECISION", {
                "trace_id": trace_id,
                "agent": agent,
                "decision": decision,
                "reason": reason
            })
    
    def log_agent_communication(
        self,
        trace_id: str,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Dict[str, Any]
    ):
        """Log agent-to-agent communication."""
        comm_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "from": from_agent,
            "to": to_agent,
            "type": message_type,
            "content": content
        }
        
        if trace_id in self.traces:
            if "communications" not in self.traces[trace_id]:
                self.traces[trace_id]["communications"] = []
            self.traces[trace_id]["communications"].append(comm_log)
        
        if self.console_mode:
            self._log_console("AGENT_COMM", {
                "trace_id": trace_id,
                "from": from_agent,
                "to": to_agent,
                "type": message_type
            })
    
    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """Get trace data."""
        return self.traces.get(trace_id)
    
    def get_trace_link(self, trace_id: str) -> str:
        """Get public trace link."""
        if self.langfuse_client:
            host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            return f"{host}/trace/{trace_id}"
        return f"console://trace/{trace_id}"
    
    def get_all_traces(self, limit: int = 50) -> List[Dict]:
        """Get recent traces."""
        traces = list(self.traces.values())
        return sorted(traces, key=lambda x: x.get("started_at", ""), reverse=True)[:limit]
    
    def _log_console(self, event_type: str, data: Dict):
        """Log to console in a structured format."""
        timestamp = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
        
        # Color codes for different event types
        colors = {
            "TRACE_START": "\033[92m",  # Green
            "TRACE_END": "\033[92m",
            "SPAN_START": "\033[94m",   # Blue
            "SPAN_END": "\033[94m",
            "DECISION": "\033[93m",     # Yellow
            "AGENT_COMM": "\033[96m",   # Cyan
        }
        reset = "\033[0m"
        color = colors.get(event_type, "")
        
        print(f"{color}[{timestamp}] 📊 {event_type}: {json.dumps(data, default=str)}{reset}")
    
    def _truncate_data(self, data: Dict, max_length: int = 200) -> Dict:
        """Truncate data for console logging."""
        if not data:
            return {}
        
        result = {}
        for key, value in data.items():
            if isinstance(value, str) and len(value) > max_length:
                result[key] = value[:max_length] + "..."
            elif isinstance(value, dict):
                result[key] = self._truncate_data(value, max_length)
            elif isinstance(value, list) and len(value) > 5:
                result[key] = value[:5] + ["..."]
            else:
                result[key] = value
        return result


# Global observability instance
observability = ObservabilityManager()
