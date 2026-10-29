"""Driven port contract for HTTP header parameter contract validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from ed_schema.core.domain.models import HeaderContract
from ed_schema.core.ports.base import DrivenPort


@runtime_checkable
class HeaderValidatorPort(DrivenPort, Protocol):
    """Secondary SPI for verifying HTTP header casing, presence, and regex rules."""

    def validate_headers(
        self,
        contract: HeaderContract,
        headers: Mapping[str, str],
    ) -> tuple[str, ...]:
        """Validates headers against contract, returning list of violation messages."""
        ...


__all__ = ["HeaderValidatorPort"]
