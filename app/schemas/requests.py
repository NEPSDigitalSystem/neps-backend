from pydantic import BaseModel, Field
from typing import Optional

class ConsentUpdateRequest(BaseModel):
    record_id: str = Field(..., description="The ID of the participant record")
    status: str = Field(..., description="The new consent status")

class ReferralCreateRequest(BaseModel):
    record_id: str = Field(..., description="The ID of the participant record")
    destination: str = Field(..., description="Destination of the referral")
    notes: Optional[str] = Field(default="", description="Optional notes for the referral")