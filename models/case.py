from langchain_core.pydantic_v1 import BaseModel, Field


class Tx(BaseModel):
    """
    Represents a blockchain transaction with relevant details including the recipient,
    value, and function call information.

    Attributes:
        description (str): A detailed description of the transaction and its purpose.
        to (str): The blockchain address of the recipient for this transaction.
        value (str): The amount of the native token being transferred in this transaction.
        function_name (str): The name of the function being invoked in this transaction.
        input_args (list[str]): A list of input arguments passed to the function in the transaction, if any.
    """

    description: str = Field(
        description="A detailed description of the transaction and its purpose."
    )
    to: str = Field(
        description="The blockchain address of the recipient for this transaction."
    )
    value: str = Field(
        description="The amount of the native token being transferred in this transaction."
    )
    function_name: str = Field(
        description="The name of the function being invoked in this transaction."
    )
    input_args: list[str] = Field(
        description="A list of input arguments passed to the function in the transaction, if any."
    )


class Case(BaseModel):
    """
    A case is a collection of transactions.
    """

    id: str = Field(description="A unique identifier for this case.")
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
