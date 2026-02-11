"""
Travel Assistant — Multi-agent orchestration with Microsoft Agent Framework.

Three workflow patterns:
  - Handoff: triage agent routes to specialists who hand off between each other
  - Sequential: weather → packing pipeline
  - Concurrent: weather + activities + booking in parallel

5 specialist agents with 12 tools, all backed by rich mock data
designed for easy swap to real APIs.
"""

from .runner import run_workflow, run_sync, get_chat_client

__all__ = ["run_workflow", "run_sync", "get_chat_client"]