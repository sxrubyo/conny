"""Integrations subsystem: external services, calendar, search, knowledge."""

from bublee.integrations.knowledge import (
    KnowledgeBase,
    format_kb_context,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MAX_CHUNKS_IN_CONTEXT,
    MIN_RELEVANCE,
)

__all__ = [
    "KnowledgeBase",
    "format_kb_context",
    "CHUNK_SIZE",
    "CHUNK_OVERLAP",
    "MAX_CHUNKS_IN_CONTEXT",
    "MIN_RELEVANCE",
]
