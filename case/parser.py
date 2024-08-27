from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from utils.model_selector import get_chat_model


model = get_chat_model(temperature=0).model


class ExtractedOutput(BaseModel):
    """The output of the extraction."""

    action: str = Field(
        description="The type of action being executed in the transaction. e.g. 'transfer', 'swap', 'stake', 'mint', 'approve', etc."
    )
    interact_with: str = Field(
        description="The contract or address that the transaction interacts with."
    )


def extract_action(description: str) -> ExtractedOutput:
    """Extract the action being performed in a transaction from a user's description."""
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a blockchain expert specialized in Ethereum transactions. Your task is to extract the action being performed in a transaction from a user's description.",
            ),
            ("user", "{description}"),
        ]
    )
    chain = prompt_template | model.with_structured_output(ExtractedOutput)
    return chain.invoke({"description": description})


# class ParsedOutput(BaseModel):
#     action: str = Field(
#         description="Specifies the type of action being executed in the transaction."
#     )
#     interact_with: str = Field(
#         description="The contract or address that the transaction is directed to or interacts with."
#     )
#     value: str = Field(
#         description="The amount of the native cryptocurrency (e.g., ETH, BNB, MATIC) involved in the transaction."
#     )
#     summary: str = Field(description="A summary of the transaction.")


# def parse_action(action: str) -> Runnable:
#     prompt_template = ChatPromptTemplate.from_messages(
#         [
#             (
#                 "system",
#                 """You are an AI assistant designed to parse and extract key transaction details from a user's description related to an Ethereum Virtual Machine (EVM) blockchain.

#     Guidelines:
#     1. If any information is missing, describe the missing information.
#     2. Default blockchain:
#         - If the user does not specify a blockchain, assume the transaction is on Ethereum.
#     3. Identify to:
#         - This represents the recipient's wallet address, smart contract, or entity. It should be the entity receiving the value or with which the action is associated.
#         - Example 1: In "Send 2 ETH to Alice", the to field would be 'Alice' since the ETH is being sent to Alice's wallet.
#         - Example 2: In "Transfer 2 USDC to Bob", the to field would be 'USDC' since the transaction is interacting with the USDC token's smart contract.
#         - Example 3: In "Swap 1 USDC for DAI on Uniswap", the to field would be 'Uniswap' since the transaction is interacting with the Uniswap smart contract.
#     4. Identify value:
#         - This is the amount of the native cryptocurrency being transferred. The value should be captured along with its unit (e.g., ETH, BNB, MATIC). That is, if the user is not sending native currency, the value should be 0.
#         - Example1: In "Send 0.5 ETH to Alice", value is '0.5';
#         - Example2: In "Send 1 USDC to Bob", value is '0'.
#         - Note: Unless explicitly stated otherwise by the user, assume that the value refers to the native currency of the blockchain network the user is referring to.
#     5. Identify action:
#         - This is the operation the user intends to perform. Actions could include sending, transferring, swapping, staking, minting, approving, etc.
#         - Example: In "Swap 1 ETH for DAI", action is 'swap'.""",
#             ),
#             ("user", "{description}"),
#         ]
#     )

#     model = get_chat_model(temperature=0).model
#     return prompt_template | model.with_structured_output(ParsedOutput)
