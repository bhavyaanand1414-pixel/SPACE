"""
Base classes and data contracts for Modular Disaster Analysis Services.

STRICT PRINCIPLES:
1. Do not claim definitive causality without in-situ ground-truth corroboration.
2. Use precise preliminary intelligence wording:
   - "Potential flood inundation"
   - "Potential earthquake-related damage"
   - "Potential cyclone-related change"
   - "Potential landslide scar"
   - "Potential wildfire burn scar"
3. Do not claim official disaster declaration status.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np


class DisasterType(str, Enum):
    FLOOD = "FLOOD"
    EARTHQUAKE = "EARTHQUAKE"
    CYCLONE = "CYCLONE"
    LANDSLIDE = "LANDSLIDE"
    WILDFIRE = "WILDFIRE"


DISASTER_CAUTIONARY_DISCLAIMER = (
    "PRELIMINARY SATELLITE INTELLIGENCE: These automated assessments represent "
    "remote-sensing derived indicators and do NOT constitute an official disaster declaration. "
    "Causality and hazard extent must be corroborated with field ground-truth and authoritative "
    "emergency management agencies."
)


@dataclass
class DisasterAssessmentResult:
    """Standard output schema for all disaster assessment modules."""
    disaster_type: DisasterType
    title: str
    affected_area_m2: float
    affected_area_km2: float
    percentage_area_affected: float
    severity_level: str                       # LOW, MEDIUM, HIGH, CRITICAL
    confidence_score: float                   # [0.0, 1.0]
    affected_regions_count: int
    geojson_features: List[Dict[str, Any]]    # Vectorized impact polygons
    modality_used: str                        # OPTICAL_MSI, SAR_SENTINEL1, or MULTI_SENSOR
    causality_wording: str                    # e.g., "Potential flood inundation detected"
    advisory_disclaimer: str = DISASTER_CAUTIONARY_DISCLAIMER
    evidence_metrics: Dict[str, Any] = field(default_factory=dict)
    model_version: str = "1.0.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BaseDisasterAnalyzer(ABC):
    """Abstract Base Class for specialized disaster assessment engines."""

    def __init__(self, disaster_type: DisasterType, model_version: str = "1.0.0"):
        self.disaster_type = disaster_type
        self.model_version = model_version

    @abstractmethod
    def analyze(
        self,
        image_before: np.ndarray,
        image_after: np.ndarray,
        resolution_m: float = 10.0,
        spatial_transform: Optional[Any] = None,
        is_sar: bool = False,
        **kwargs,
    ) -> DisasterAssessmentResult:
        """
        Execute disaster-specific damage/inundation assessment on multi-temporal images.
        """
        ...
