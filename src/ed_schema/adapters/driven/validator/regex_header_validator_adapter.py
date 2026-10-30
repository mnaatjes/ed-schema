"""Header validator adapter implementing HeaderValidatorPort."""

from __future__ import annotations

import re
from collections.abc import Mapping

from ed_schema.core.domain.models import HeaderContract
from ed_schema.core.ports.driven.header_validator_port import HeaderValidatorPort


class RegexHeaderValidatorAdapter(HeaderValidatorPort):
    """Secondary SPI adapter for verifying HTTP header casing, presence, and regex rules."""

    def validate_headers(
        self,
        contract: HeaderContract,
        headers: Mapping[str, str],
    ) -> tuple[str, ...]:
        """Validates headers against contract, returning list of violation messages.

        Args:
            contract: The HeaderContract defining parameter requirements.
            headers: Case-insensitive mapping of provided HTTP headers.

        Returns:
            Tuple of violation messages. Empty tuple indicates full compliance.
        """
        # Case-insensitive header normalization
        normalized_headers: dict[str, str] = {
            str(key).strip().lower(): str(val) for key, val in headers.items()
        }

        violations: list[str] = []

        for param in contract.parameters:
            param_key = param.name.strip().lower()

            if param_key not in normalized_headers:
                if param.required:
                    violations.append(f"Missing required header: '{param.name}'")
                continue

            value = normalized_headers[param_key]

            if param.regex_pattern is not None:
                try:
                    if not re.search(param.regex_pattern, value):
                        msg = (
                            f"Header '{param.name}' value '{value}' does not match "
                            f"required pattern '{param.regex_pattern}'"
                        )
                        violations.append(msg)
                except re.error as exc:
                    msg = (
                        f"Header contract '{param.name}' contains invalid regex "
                        f"'{param.regex_pattern}': {exc}"
                    )
                    violations.append(msg)

        violations.sort()
        return tuple(violations)


__all__ = ("RegexHeaderValidatorAdapter",)
