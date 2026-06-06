"""Canonical financial facts and generated consumer views."""

from .facts import FactCandidate, FactsRepository, Period, resolve_period_ids
from .legacy import LegacyMigrator, MigrationResult

__all__ = [
    "FactCandidate",
    "FactsRepository",
    "LegacyMigrator",
    "MigrationResult",
    "Period",
    "resolve_period_ids",
]
