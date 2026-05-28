from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ContractBaseModel(BaseModel):
    """Base model for shared contracts.

    During early development we allow extra fields because the event structure may
    still be evolving. Later, this can be changed to extra="forbid" if we want
    stricter validation.
    """

    model_config = ConfigDict(extra="allow")


class Event(ContractBaseModel):
    id: int
    scenario_id: Optional[int] = None
    timestamp: Optional[str] = None
    protocol: Optional[str] = None
    protocol_data: List[Any] = Field(default_factory=list)
    tcp_ip: Optional[dict[str, Any]] = None


class EventsFile(ContractBaseModel):
    events: List[Event]
