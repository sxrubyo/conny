"""
bublee/core/ — Clean public API for Bublee v9.0.

Exports the main engine components without requiring direct bublee.py imports.
This module bridges the legacy monolith (bublee.py) with the new modular architecture.
"""
from bublee_memory_engine import memory_engine, BubleeMemoryEngine
from bublee_uncertainty import uncertainty_detector, UncertaintyDetector
from bublee_voice import voice, BubleeVoice
from bublee_nova_proxy import NovaLLMProxy
from src.interfaces.web.admin_api import router as admin_router
from bublee_cron import init_scheduler, shutdown_scheduler

__all__ = [
    "memory_engine",
    "BubleeMemoryEngine",
    "uncertainty_detector",
    "UncertaintyDetector",
    "voice",
    "BubleeVoice",
    "NovaLLMProxy",
    "admin_router",
    "init_scheduler",
    "shutdown_scheduler",
]
