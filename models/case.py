from langchain_core.pydantic_v1 import BaseModel, Field


class Transaction(BaseModel):
    """
    A transaction is an action taking place on a blockchain network.
    """

    description: str = Field(
        description="A detailed description of the transaction and its purpose."
    )


class BatchCase(BaseModel):
    """
    A batch case is a collection of transactions.
    """

    id: str = Field(
        description="A unique identifier assigned to this case, used to distinguish it from others."
    )
    description: str = Field(
        description="A comprehensive description providing context, background, and the purpose of the batch case."
    )
    # total_steps: int = Field(
    #     description="The total number of transactions included in this case."
    # )
    steps: list[Transaction] = Field(
        description="A sequential list of transactions (Tx), where each step represents to a single transaction."
    )


class CaseOutput(BaseModel):
    cases: list[BatchCase] = Field(
        description="A list containing multiple case instances."
    )
