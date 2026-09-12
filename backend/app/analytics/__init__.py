"""Phase 2 analytics package (lifestyle intelligence + pattern detection).

Kept fully separate from the HTTP/database layers so the scientific code can be
tested and evolved independently. The FastAPI layer (``app/services`` /
``app/api``) only orchestrates calls into here.

The engine deliberately has NO disease prediction, NO medical risk scores and
NO health claims - it only learns "what appears to work for YOU".
"""

from app.analytics.config import AnalyticsConfig
from app.analytics.engine import AnalyticsBundle, AnalyticsEngine

__all__ = ["AnalyticsConfig", "AnalyticsBundle", "AnalyticsEngine"]