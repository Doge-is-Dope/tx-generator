from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from utils.model_selector import get_chat_model


model = get_chat_model(temperature=0).model


class ParsedOutput(BaseModel):
    """The output of the extraction."""

    action: str = Field(
        description="The type of action being executed in the transaction. e.g. 'transfer', 'swap', 'stake', 'mint', 'approve', etc."
    )
    interact_with: str = Field(
        description="The contract or address that the transaction interacts with."
    )


def parse_description(description: str) -> ParsedOutput:
    """Extract the action being performed and the contract or address that the transaction interacts with from a user's description."""
    system_prompt = SystemMessage(
        content="""You are a blockchain expert specialized in Ethereum transactions. 
                Your task is to extract the action being performed in a transaction from a user's description.
                - action: the type of action being executed in the transaction. e.g. 'transfer', 'swap', 'stake', 'mint', 'approve', etc.
                - interact_with: the contract or address that the transaction interacts with.

                Examples:
                - Given the description: "Send 0.03 ETH to Alice", the output should be:
                `action: transfer, interact_with: Alice's address`
                - Given the description: "Approve 400 stETH to be used by Uniswap", the output should be:
                `action: approve, interact_with: stETH's contract address`
                """,
    )
    prompt_template = ChatPromptTemplate.from_messages(
        [system_prompt, HumanMessage(content=description)]
    )
    chain = prompt_template | model.with_structured_output(ParsedOutput)
    return chain.invoke({"description": description})
