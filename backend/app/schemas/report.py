"""
Pydantic Schemas for Geospatial PDF Report Generation and Metadata.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReportGenerationRequest(BaseModel):
    """Payload to trigger PDF report generation."""
    title: Optional[str] = Field(default="ISRO Multi-Temporal Satellite Change Intelligence Report")
    study_area: Optional[str] = Field(default="Guwahati Urban Corridor")
    include_methodology: bool = True
    include_spectral_evidence: bool = True


class ReportMetadataResponse(BaseModel):
    """Summary metadata for a generated PDF report."""
    report_id: str
    analysis_id: str
    study_area: str
    filename: str
    file_size_bytes: int
    download_url: str
    total_area_km2: float
    changed_area_km2: float
    percentage_changed: float
    dominant_category: str
    generated_at: str
    status: str = "COMPLETED"
