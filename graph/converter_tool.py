import os
from typing import Literal
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode

from graph.tools import tools

# Set up tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "converter"


class TransactionParams(BaseModel):
    """
    Convert the final result into transaction parameters.
    """

    from_address: str = Field(description="The address of the sender (from)")
    to_address: str = Field(description="The address being interacted with (to)")
    data: str = Field("0x", description="Transaction data in hex, start with '0x'")
    value: str = Field("0x0", description="Amount of native token to send, in hex")

    @validator("from_address", "to_address")
    def check_address_format(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Address must start with '0x'")
        if len(v) != 42:
            raise ValueError("Address must be 42 characters long")
        return v

    @validator("value")
    def check_value_format(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Value must start with '0x'")
        return v

    @validator("data")
    def check_data_format(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Data must start with '0x'")
        return v

    def __str__(self):
        return f"From: {self.from_address}\nTo: {self.to_address}\nData: {self.data}\nValue: {self.value}"


tools = tools + [TransactionParams]
model = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)
model_with_tools = model.bind_tools(tools)


class AgentInput(MessagesState):
    pass


class AgentOutput(MessagesState):
    response: TransactionParams


class AgentState(MessagesState):
    response: TransactionParams


def call_model(state: AgentState):
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def convert(state: AgentState):
    messages = state["messages"]
    # Construct tx params from the arguments of the last tool call
    tx_params = TransactionParams(**messages[-1].tool_calls[0]["args"])
    return {"response": tx_params}


def should_continue(state: AgentState) -> Literal["convert", "continue"]:
    messages = state["messages"]
    last_message = messages[-1]
    if (
        len(last_message.tool_calls) == 1
        and last_message.tool_calls[0]["name"] == "TransactionParams"
    ):
        return "convert"

    return "continue"


workflow = StateGraph(AgentState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("converter", convert)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent", should_continue, {"convert": "converter", "continue": "tools"}
)
workflow.add_edge("tools", "agent")
workflow.set_finish_point("converter")

app = workflow.compile()


system_prompt = """Interpret the provided description to generate Ethereum transaction parameters using the following tools:
-------------
- fetch_contract_abi: Retrieve the ABI for a contract by address or function name.
- get_contract_address_by_name: Get a contract address using a protocol or token name.
- resolve_ens: Convert an ENS domain to an Ethereum address.
- convert_to_checksum_address: Format an Ethereum address to checksum format.
- encode_function_call: Encode a function call and its arguments using the ABI.
- get_token_info: Retrieve token details (name, symbol, decimals) by address.
- convert_to_smallest_unit: Convert a token amount to its smallest unit (e.g., wei) based on decimals.
- convert_dec_to_hex: Convert a decimal integer to a hexadecimal string.
- get_current_timestamp: Get the current timestamp in seconds.
-------------
Once you have the transaction encoded data (using tool 'encode_function_call'), finalize by using `convert_to_tx_params` to create a TransactionParams object and return it.
Sender address: {from_address}
Current time: {current_time}"""


async def generate_tx_params(description: str, from_address: str) -> TransactionParams:
    system_message = SystemMessage(
        system_prompt.format(from_address=from_address, current_time=datetime.now())
    )
    input = {"messages": [system_message, HumanMessage(description)]}
    result = await app.ainvoke(input)
    return result["response"]
