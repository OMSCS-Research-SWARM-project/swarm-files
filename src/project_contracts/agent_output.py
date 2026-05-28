from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ContractBaseModel(BaseModel):
    """Base model for shared contracts.

    We currently allow extra fields during development.
    Once the schema is stable, switch this to extra="forbid".
    """

    model_config = ConfigDict(extra="allow")


class EventClassification(ContractBaseModel):
    event_id: int
    scenario_id: Optional[int] = None
    classification: str
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    cve: Optional[str] = None


class AgentOutput(ContractBaseModel):
    classifications: List[EventClassification]
    mapped_cves: List[str] = Field(default_factory=list)
