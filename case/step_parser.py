from langchain_core.pydantic_v1 import BaseModel, Field
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
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a blockchain expert specialized in Ethereum transactions. Your task is to extract the action being performed in a transaction from a user's description.",
            ),
            ("user", "{description}"),
        ]
    )
    chain = prompt_template | model.with_structured_output(ParsedOutput)
    return chain.invoke({"description": description})
