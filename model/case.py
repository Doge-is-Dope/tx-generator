from langchain_core.pydantic_v1 import BaseModel, Field
from .tx import Tx


class Case(BaseModel):
    case_id: str = Field(description="A unique identifier for this case.")
    description: str = Field(
        description="A detailed description outlining the context and purpose of the case."
    )
    total_steps: int = Field(
        description="The total number of transactions of the case."
    )
    steps: list[Tx] = Field(
        description="A sequential list of transactions (Tx) that are part of the case, where each step corresponds to a single transaction."
    )


class CaseOutput(BaseModel):
    cases: list[Case] = Field(description="A list containing multiple case instances.")
