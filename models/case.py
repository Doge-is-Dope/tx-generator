from langchain_core.pydantic_v1 import BaseModel, Field


# class Tx(BaseModel):
#     """
#     Represents a blockchain transaction with relevant details including the recipient,
#     value, and function call information.

#     Attributes:
#         description (str): A detailed description of the transaction and its purpose.
#         to (str): The blockchain address of the recipient for this transaction.
#         value (str): The amount of the native token being transferred in this transaction.
#         function_name (str): The name of the function being invoked in this transaction.
#         input_args (list[str]): A list of input arguments passed to the function in the transaction, if any.
#     """

#     description: str = Field(
#         description="A detailed description of the transaction and its purpose."
#     )
#     to: str = Field(
#         description="The blockchain address of the recipient for this transaction."
#     )
#     value: str = Field(
#         description="The amount of the native token being transferred in this transaction."
#     )
#     function_name: str = Field(
#         description="The name of the function being invoked in this transaction."
#     )
#     input_args: list[str] = Field(
#         description="A list of input arguments passed to the function in the transaction, if any."
#     )


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
    total_steps: int = Field(
        description="The total number of transactions included in this case."
    )
    steps: list[Transaction] = Field(
        description="A sequential list of transactions (Tx), where each step represents to a single transaction."
    )


class CaseOutput(BaseModel):
    cases: list[BatchCase] = Field(
        description="A list containing multiple case instances."
    )
