from pydantic import BaseModel
from typing import Optional


class UserAccountContext(BaseModel):

    model_config = {"extra": "forbid"}

    customer_id: int
    name: str
    tier: str = "basic"
    email: Optional[str] = None  

    def is_premium_customer(self):
        return self.tier != "basic"

class InputGuardRailOutput(BaseModel):

    model_config = {"extra": "forbid"}

    is_off_topic: bool
    reason: str


class ComplaintsOutputGuardRailOutput(BaseModel):

    model_config = {"extra": "forbid"}

    contains_off_topic: bool
    contains_billing_data: bool
    contains_account_data: bool
    is_off_topic: bool
    reason: str
    contains_technical_details: bool = False  

    

class HandoffData(BaseModel):

    model_config = {"extra": "forbid"}

    to_agent_name: str
    issue_type: str
    issue_description: str
    reason: str
