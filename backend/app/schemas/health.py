from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Status code of the service")
    service: str = Field(default="SIH1518 backend", description="Name of the running service")
    version: Optional[str] = Field(default="1.0.0", description="Backend service version")
    database: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Database connectivity status")
