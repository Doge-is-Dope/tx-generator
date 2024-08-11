from langchain_core.pydantic_v1 import BaseModel, Field


class Tx(BaseModel):
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
