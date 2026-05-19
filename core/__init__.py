"""
conny/core/ — Clean public API for Conny v9.0.

Exports the main engine components without requiring direct conny.py imports.
This module bridges the legacy monolith (conny.py) with the new modular architecture.
"""
from conny_memory_engine import memory_engine, ConnyMemoryEngine
from conny_uncertainty import uncertainty_detector, UncertaintyDetector
from conny_voice import voice, ConnyVoice
from conny_nova_proxy import NovaLLMProxy
from conny_admin_api import router as admin_router
from conny_cron import init_scheduler, shutdown_scheduler

__all__ = [
    "memory_engine",
    "ConnyMemoryEngine",
    "uncertainty_detector",
    "UncertaintyDetector",
    "voice",
    "ConnyVoice",
    "NovaLLMProxy",
    "admin_router",
    "init_scheduler",
    "shutdown_scheduler",
]
