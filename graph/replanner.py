import os
from typing import List, Union
from decimal import Decimal

import asyncio
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from graph.state import PlanSimulateState


os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "replanner"


def convert_hex_amount_to_decimal(raw_amount: str, decimals: int) -> str:
    """
    Convert a raw hexadecimal amount to a decimal amount.

    This function takes a hexadecimal string representing a raw amount and converts it
    to a floating-point number, assuming 18 decimal places (common for Ethereum-based tokens).

    Args:
        raw_amount (str): A hexadecimal string representing the raw amount.
        decimals (int): The number of decimals for the token (default is 18).

    Returns:
        str: The converted amount as a string, preserving high precision.

    Example:
        >>> convert_raw_amount_to_readable_amount("0x6a94d74f42ffff", 18)
        0.029999999999999999
    """
    raw_decimal = Decimal(int(raw_amount, 16))
    result = raw_decimal / Decimal(10**decimals)
    return str(result.normalize())


class Plan(BaseModel):
    """The updated plan"""

    steps: List[str]


user_prompt = """
Your task is to update the next steps based on the simulated transactions.

Context:
- User's address: 
{from_address}
- Simulated transactions: 
{simulated_txs}
- Next steps: 
{remaining_steps}

Instructions:
1. Review the simulated transactions and determine if any changes are needed in the next steps.
2. Update steps with relevant details from the simulations, such as token amounts or addresses.
3. Return the revised plan, reflecting only the necessary updates.

Example:
If the step is "Approve USDC for Uniswap" and the simulation confirms a token amount:
- Extract the amount from the simulation result. e.g., Received {{amount_string}} USDC.
- Update the step. e.g., "Approve {{amount_string}} USDC for Uniswap."

Important:
- Only modify steps that are still pending.
- Do not include completed or simulated steps.
"""

system_prompt = "You are a blockchain expert specializing in EVM transactions."

# Create the prompt
prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("user", user_prompt)]
)
model = ChatOpenAI(model="gpt-4o", temperature=0)
replanner = RunnablePassthrough() | prompt | model.with_structured_output(Plan)


async def replan_step(state: PlanSimulateState):
    from_address = state["from_address"]
    steps = state["steps"]
    # Build the simulated transactions list
    simulated_txs = await _build_simulated_txs(state["simulated_txs"], from_address)
    # Run the chain and await the response
    response = await replanner.ainvoke(
        {
            "from_address": from_address,
            "simulated_txs": "\n".join(simulated_txs),
            "remaining_steps": steps,
        }
    )
    return {"steps": response.steps}


async def _build_simulated_txs(simulated_txs_data, from_address):
    simulated_txs = []

    # Process each simulated transaction
    for index, (desc, _, asset_changes) in enumerate(simulated_txs_data, 1):
        simulated_txs.append(f"{index}. {desc}")

        # Concurrently resolve asset changes
        tx_lines = await asyncio.gather(
            *[_process_asset_change(asset, from_address) for asset in asset_changes]
        )
        simulated_txs.extend(tx_lines)
        simulated_txs.append("")  # Empty line for spacing

    return simulated_txs


async def _process_asset_change(asset, from_address) -> str:
    # Convert the amount asynchronously
    amount = convert_hex_amount_to_decimal(asset.raw_amount, asset.decimals)

    # Determine whether the asset was sent or received
    if asset.sender == from_address:
        return f"  - Sent {amount} {asset.symbol}"
    elif asset.receiver == from_address:
        return f"  - Received {amount} {asset.symbol}"
    return ""
