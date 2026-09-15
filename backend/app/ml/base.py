"""
Base class and data contracts for Satellite Change Detectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class ChangeRegionFeature:
    """Vectorized change polygon feature with hierarchical classification and evidence."""
    region_index: int
    geojson_geometry: Dict[str, Any]
    centroid_lat: float
    centroid_lon: float
    area_m2: float
    area_km2: float
    perimeter_m: Optional[float] = None
    bbox: List[float] = field(default_factory=list)  # [min_x, min_y, max_x, max_y]
    mean_confidence: float = 0.8
    spectral_difference: float = 0.0
    category: str = "HUMAN"
    subtype: str = "Building"
    subcategory: str = "Building"
    severity_level: str = "MEDIUM"
    evidence: Dict[str, Any] = field(default_factory=dict)
    model_version: str = "1.0.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ChangeDetectionResult:
    """Result of running a change detector on an image pair."""
    change_mask: np.ndarray             # (H, W) uint8 (0 or 255)
    probability_map: np.ndarray         # (H, W) float32 [0.0, 1.0]
    total_pixels_changed: int
    total_area_m2: float
    total_area_km2: float
    total_area_changed_m2: float
    total_area_changed_km2: float
    percentage_changed: float
    region_count: int
    regions: List[ChangeRegionFeature]
    model_name: str
    model_version: str
    label: str = "Baseline / Demo Result"
    disclaimer: str = "Generated using deterministic spectral differencing baseline. Never present baseline output as trained AI performance."
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseChangeDetector(ABC):
    """Abstract Base Class for all Change Detection engines."""

    def __init__(self, model_name: str, model_version: str):
        self.model_name = model_name
        self.model_version = model_version

    @abstractmethod
    def detect_change(
        self,
        image1: np.ndarray,
        image2: np.ndarray,
        spatial_transform: Optional[Any] = None,
        crs: Optional[str] = None,
        resolution_m: float = 10.0,
        confidence_threshold: float = 0.5,
        **kwargs,
    ) -> ChangeDetectionResult:
        """
        Execute change detection inference on preprocessed (C, H, W) normalized image pair.
        """
        ...
