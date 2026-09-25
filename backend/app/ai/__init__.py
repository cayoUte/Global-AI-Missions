"""Maya's narrator layer: a provider-agnostic coach port, a Claude adapter and a deterministic mock.

Entry points: get_coach_provider() (used by submit, CR-004), service.generate_feedback(),
service.update_memory(). Provider SDKs are imported only inside this package.
"""

from app.ai.factory import get_coach_provider

__all__ = ["get_coach_provider"]
