import os
from datetime import datetime
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI

from graph.tools import tools
from graph.tools.simulation import TransactionParams


os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "converter"

model = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)
model_with_tools = model.bind_tools(tools)
model_with_structured_output = model.with_structured_output(TransactionParams)


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
    tx_params = model_with_structured_output.invoke(messages)
    return {"response": tx_params}


def should_continue(state: AgentState) -> Literal["convert", "continue"]:
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
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

converter = workflow.compile()


system_prompt = """
Interpret the provided description to generate Ethereum transaction parameters using the following tools:
-------------
- fetch_contract_abi: Retrieve the ABI for a contract by address or function name.
- get_contract_address_by_name: Get a contract address using a protocol or token name.
- resolve_ens: Convert an ENS domain to an Ethereum address.
- convert_to_checksum_address: Format an Ethereum address to checksum format.
- encode_function_call: Encode a function call and its arguments using the ABI.
- get_token_info: Retrieve token details (name, symbol, decimals) by address.
- convert_to_smallest_unit: Convert a token amount to its smallest unit (e.g., wei) based on decimals.
- convert_dec_to_hex: Convert a decimal integer to a hexadecimal string.
- get_current_timestamp: Get the current timestamp in seconds. Use this tool to set transaction deadlines or for time-sensitive operations.
-------------
Once you have the transaction encoded data, return the transaction parameters (from, to, data, value). 
Sender Address: {from_address}
Current Time: {current_time}
"""


async def generate_tx_params(description: str, from_address: str) -> TransactionParams:
    system_message = SystemMessage(
        system_prompt.format(from_address=from_address, current_time=datetime.now())
    )
    input = {"messages": [system_message, HumanMessage(description)]}
    result = await converter.ainvoke(input)
    # print(f"generate_tx_params result: {result}")
    return result["response"]
