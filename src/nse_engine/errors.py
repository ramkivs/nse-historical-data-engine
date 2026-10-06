"""Fail-closed error types for the W1 reference parser.

Design rule (D07 §7): a source record that cannot be parsed safely under the governed
canonical contract is never guessed, coerced or silently dropped. Member-level failures
raise; row-level failures are quarantined with the raw line retained.
"""

from __future__ import annotations


class NseEngineError(Exception):
    """Base class for all W1 engine errors."""


class MemberDecodeError(NseEngineError):
    """The member bytes are not decodable as governed text (D05 §7.6: fail loudly)."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class BomNotToleratedError(MemberDecodeError):
    """A UTF-8 BOM is present.

    D05 §7 authorizes exactly two member-header tolerances (trailing empty legacy field
    and the two documented legacy timestamp forms). No BOM tolerance is authorized by
    D05/D07, and no BOM was observed in the corpus; stripping one would be an
    unauthorized tolerance and silently mutating raw bytes, so W1 fails closed.
    """

    def __init__(self) -> None:
        super().__init__(
            "member begins with a UTF-8 BOM; BOM tolerance is not authorized by D05 §7 — refusing to "
            "strip bytes silently (fail-closed)"
        )


class CarriageReturnNotFollowedByLineFeedError(MemberDecodeError):
    """A bare CR appears; only CRLF and LF line endings are governed (D05 §9)."""

    def __init__(self, line_number: int) -> None:
        super().__init__(
            "carriage return without a following line feed at line %d; D05 §9 governs CRLF/LF only and "
            "no CR-only tolerance is authorized (fail-closed)" % line_number
        )


class HeaderUnrecognizedError(NseEngineError):
    """The member header matches neither governed family header.

    D05 §7.3: a member whose header matches neither family header (after the trailing-empty
    tolerance) is a parse failure — quarantine, not best-effort mapping.
    """

    def __init__(self, physical_width: int, first_fields: tuple, detail: str = "") -> None:
        self.physical_width = physical_width
        self.first_fields = first_fields
        self.detail = detail
        message = (
            "header matches neither %s (13 fields or 14 with trailing empty field) nor %s (34 fields); "
            "physical width=%d, leading fields=%r"
            % ("legacy13", "udiff34", physical_width, first_fields)
        )
        if detail:
            message += "; " + detail
        super().__init__(message)


class GovernanceBlockedError(NseEngineError):
    """A requested operation requires a semantic decision that governance has not made.

    Raised by the fail-closed stubs in :mod:`nse_engine.blocked` (D07 §13-B/C, D07 §14).
    The engine never substitutes a default: it stops and names the dependency.
    """

    def __init__(self, dependency_id: str, operation: str, reason: str, reference: str) -> None:
        self.dependency_id = dependency_id
        self.operation = operation
        self.reason = reason
        self.reference = reference
        super().__init__(
            "%s is blocked by unresolved governance dependency %s: %s [%s]"
            % (operation, dependency_id, reason, reference)
        )


class EmptyMemberError(NseEngineError):
    """The member contains no header line at all."""

    def __init__(self) -> None:
        super().__init__("member contains no header line (D05 §7.5 one-row-per-record assumption)")
