"""
The simulation module is responsible for simulating transactions on Tenderly.

Functions:
- simulate_transaction: Simulates a transaction on Tenderly and returns SimulationResult.

Classes:
- TransactionParams: Transaction parameters for the input of the simulation.
- SimulationResult: Simulation results including asset changes and error messages.
"""

import os
import requests
from typing import List, Optional

from langchain_core.pydantic_v1 import BaseModel, Field, validator


class TransactionParams(BaseModel):
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


class AssetChange(BaseModel):
    type: str
    name: str
    symbol: str
    decimals: int
    raw_amount: str
    sender: str
    receiver: str
    contract_address: Optional[str]


class TransactionResult(BaseModel):
    """The result of a single transaction."""

    # The address that initiated this transaction. Should match SimulationResult's from_address.
    from_address: str = ""
    # The address that the transaction is sent to
    to_address: str = ""
    asset_changes: List[AssetChange] = []
    error: str = ""

    def __str__(self) -> str:
        status = "successful" if not self.error else "failed"
        transaction_info = [f"Transaction was {status}."]
        # Add error if any
        if self.error:
            transaction_info.append(self.error)
        # Add information about each asset change
        for asset_change in self.asset_changes:
            is_sender = asset_change.sender.lower() == self.from_address.lower()
            is_receiver = asset_change.receiver.lower() == self.from_address.lower()

            if is_sender and is_receiver:
                raise Exception("Sender and receiver shall not be the same")

            outgoing_sign = "-" if is_sender else "+"
            amount = int(asset_change.raw_amount, 16)
            asset_type = asset_change.contract_address or "Native"
            info_message = f"💰 {asset_change.symbol.upper()} ({asset_type}): {outgoing_sign}{amount:,} ({asset_change.raw_amount})"
            transaction_info.append(info_message)
        return "\n".join(transaction_info)


class SimulationResult(BaseModel):
    from_address: str  # The address that initiated the first transaction
    tx_results: List[TransactionResult]

    @validator("tx_results")
    def check_from_address(cls, v, values):
        from_address = values.get("from_address", "").lower()
        if from_address:
            for tx in v:
                if tx.from_address.lower() != from_address:
                    raise ValueError(
                        f"From address mismatch: expected {from_address}, got {tx.from_address}"
                    )
        return v

    def pretty_print(self):
        for i, tx_result in enumerate(self.tx_results):
            print(f"#{i + 1}: {tx_result}")
            print("-------------------------------------")


def simulate_transaction(transactions: List[TransactionParams]) -> SimulationResult:
    """
    Simulate a transaction on Tenderly.

    Args:
        transactions (List[TransactionParams]): List of transactions to simulate.

    Returns:
        SimulationResult: The result of the simulation.
    """
    TENDERLY_API_KEY = os.getenv("TENDERLY_API_KEY")
    url = f"https://mainnet.gateway.tenderly.co/{TENDERLY_API_KEY}"
    data = {
        "id": 0,
        "jsonrpc": "2.0",
        "method": "tenderly_simulateBundle",
        "params": [
            [
                {
                    "from": tx.from_address,
                    "to": tx.to_address,
                    "data": tx.data,
                    "value": tx.value,
                }
                for tx in transactions
            ],
            "latest",
        ],
    }
    response = requests.post(url, json=data).json()

    if "error" in response:
        raise Exception(f"Simulation API error: {response['error']['message']}")
    if "result" in response:
        sender = transactions[0].from_address
        return _format_simulation_result(sender, response["result"])
    raise Exception(f"Unexpected response: {response}")


def _extract_error_from_trace(trace_list: list[dict]) -> str:
    """Extract error and error reason from trace list if applicable."""
    for trace in reversed(trace_list):
        error = trace.get("error")
        if error:
            error_reason = trace.get("errorReason", "")
            return f"{error}: {error_reason}" if error_reason else error
    return ""


def _extract_first_call_from_trace(trace_list: list[dict]) -> tuple[str, str]:
    """Extract the 'from' and 'to' addresses from the first call in the trace list."""
    if trace_list:
        first_trace = trace_list[0]
        return first_trace.get("from", ""), first_trace.get("to", "")
    return "", ""


def _format_simulation_result(sender: str, results: list[dict]) -> SimulationResult:
    """Formats the simulation results including asset changes and errors."""
    if not results:
        raise Exception("No results from simulation")

    tx_results = []

    for result in results:
        trace = result.get("trace", [])
        from_address, to_address = _extract_first_call_from_trace(trace)

        # Handle failed transaction
        if not result.get("status"):
            error = _extract_error_from_trace(trace)
            tx_results.append(
                TransactionResult(
                    from_address=from_address, to_address=to_address, error=error
                )
            )
            if error:
                continue  # Skip further processing for failed transactions

        # Process asset changes
        asset_changes = [
            AssetChange(
                type=asset.get("type"),
                name=asset["assetInfo"].get("name", ""),
                symbol=asset["assetInfo"].get("symbol", ""),
                decimals=asset["assetInfo"].get("decimals", 0),
                raw_amount=asset["rawAmount"],
                sender=asset["from"],
                receiver=asset["to"],
                contract_address=asset["assetInfo"].get("contractAddress", ""),
            )
            for asset in result.get("assetChanges", [])
        ]

        tx_results.append(
            TransactionResult(
                from_address=from_address,
                to_address=to_address,
                asset_changes=asset_changes,
            )
        )

    return SimulationResult(from_address=sender, tx_results=tx_results)


if __name__ == "__main__":
    import time
    import json
    from web3 import Web3

    dummy_from_address = "0x2d4d2A025b10C09BDbd794B4FCe4F7ea8C7d7bB4"
    dummy_to_address = "0x8c575b178927fF9A70804B8b4F7622F7666bB360"
    usdt_address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    usdc_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    uniswap_v2_router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

    with open("abi/erc20.json") as file:
        erc20_abi = json.load(file)

    with open("abi/uniswap_v2_router.json") as file:
        uniswap_v2_router_abi = json.load(file)

    INFURA_API_KEY = os.getenv("INFURA_API_KEY")
    w3 = Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"))

    usdc_contract = w3.eth.contract(abi=erc20_abi)
    uniswap_contract = w3.eth.contract(abi=uniswap_v2_router_abi)

    # Approve 1000000 USDC to Uniswap V2 Router
    approve_encoded_data = usdc_contract.encode_abi(
        "approve", args=[uniswap_v2_router_address, 1_000_000]
    )

    # Swap 1000000 USDC to USDT
    swap_encoded_data = uniswap_contract.encode_abi(
        "swapExactTokensForTokens",
        [
            1_000_000,
            0,
            [usdc_address, usdt_address],
            dummy_from_address,
            int(time.time()) + 500,
        ],
    )

    result = simulate_transaction(
        [
            TransactionParams(
                from_address=dummy_from_address,
                to_address=usdc_address,
                data=approve_encoded_data,
                value="0x0",
            ),
            TransactionParams(
                from_address=dummy_from_address,
                to_address=uniswap_v2_router_address,
                data=swap_encoded_data,
                value="0x0",
            ),
            TransactionParams(
                from_address=dummy_from_address,
                to_address=dummy_to_address,
                data="0x",
                value="0x7b",
            ),
        ]
    )
    result.pretty_print()
