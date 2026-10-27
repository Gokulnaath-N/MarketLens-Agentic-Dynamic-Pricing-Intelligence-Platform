"""License and terms evaluation module for dataset candidate sources.

Enforces hard-gate validation: candidate datasets cannot be downloaded or marked
acceptable unless their license terms and access credentials meet compliance rules.
"""

from __future__ import annotations

from typing import Tuple
from marketlens.datasets.models import CandidateDataset, LicenseInfo


class LicenseEvaluationError(Exception):
    """Raised when license terms or access routes fail validation."""

    pass


def evaluate_hard_gates(candidate: CandidateDataset, has_credentials: bool = False) -> Tuple[bool, str]:
    """Evaluate mandatory compliance and access gates for a candidate dataset.

    Hard gates:
    1. License must be explicitly documented and permit academic prototype research.
    2. If authentication/credentials are required (e.g. Kaggle API), valid credentials
       must be configured in the local environment.
    3. Direct, permitted acquisition route must be available (no unauthorized scraping).

    Args:
        candidate: CandidateDataset instance.
        has_credentials: True if credentials for this source are available in the environment.

    Returns:
        Tuple of (passed: bool, reason: str).
    """
    # Check 1: License validity
    if not candidate.license.license_name or candidate.license.license_name.strip() == "":
        return False, "Blocked: License name is missing or unknown."

    if not candidate.license.academic_allowed:
        return False, f"Blocked: License '{candidate.license.license_name}' does not permit research/academic use."

    # Check 2: Credential requirements
    if candidate.requires_auth and not has_credentials:
        return (
            False,
            f"Blocked (Missing Credentials): Source '{candidate.name}' requires {candidate.auth_type or 'credentials'}, but none are configured.",
        )

    # Check 3: Verified official URL
    if not candidate.official_url or not candidate.official_url.startswith("https://"):
        return False, "Blocked: Missing or insecure (non-HTTPS) official source URL."

    return True, "Hard gates passed: License and access conditions satisfied."
