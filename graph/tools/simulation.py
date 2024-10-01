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

from pydantic import BaseModel, Field, field_validator
from langchain_core.tools import tool

from models.tx_params import TransactionParams


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
    """
    The result of a single transaction.

    Attributes:
        from_address (str): The address that initiated the transaction. Should match the `from_address` in the SimulationResult.
        to_address (str): The address that the transaction was sent to.
        asset_changes (List[AssetChange]): A list of asset changes (transfers, token movements) that occurred due to the transaction.
        error (str, default=''): Error message, if the transaction encountered any issues. Defaults to an empty string if no error occurred.

    Purpose:
        This class captures the outcome of a transaction, including the initiator, recipient, any asset changes, and potential errors.
    """

    from_address: str = Field(
        "", description="The address that initiated the transaction"
    )
    to_address: str = Field(
        "", description="The address that the transaction was sent to"
    )
    asset_changes: List[AssetChange] = Field(
        [], description="List of asset changes that occurred due to the transaction"
    )
    error: str = Field(
        "", description="Error message, if the transaction encountered any issues"
    )

    def pretty_print(self):
        from decimal import Decimal

        # Print error message if the transaction failed
        if self.error:
            print(f"Error: {self.error}")

        from_address = self.from_address.lower()

        # Iterate over asset changes
        for asset_change in self.asset_changes:
            is_sender = asset_change.sender.lower() == from_address
            is_receiver = asset_change.receiver.lower() == from_address

            # Ensure the sender and receiver are not the same
            if is_sender and is_receiver:
                raise ValueError("Sender and receiver cannot be the same")

            # Determine transaction direction (outgoing/incoming)
            transaction_sign = "-" if is_sender else "+"
            contract_address = (
                f"({asset_change.contract_address})"
                if asset_change.contract_address
                else ""
            )
            raw_amount_dec = int(asset_change.raw_amount, 16)
            formatted_amount = Decimal(raw_amount_dec) / Decimal(
                10**asset_change.decimals
            )
            formatted_amount_str = (
                "{:f}".format(formatted_amount).rstrip("0").rstrip(".")
            )

            asset_symbol = asset_change.symbol.upper()
            print(
                f"Amount: {transaction_sign}{formatted_amount_str} {asset_symbol} {contract_address or ''}\n"
                f"- Hex: {asset_change.raw_amount}\n"
                f"- Decimal: {raw_amount_dec:_}"
            )


class SimulationResult(BaseModel):
    from_address: str  # The address that initiated the first transaction
    tx_results: List[TransactionResult]

    @field_validator("tx_results")
    def check_from_address(cls, v, values):
        from_address = values.data["from_address"].lower()
        if from_address:
            for tx in v:
                if tx.from_address.lower() != from_address:
                    raise ValueError(
                        f"From address mismatch: expected {tx.from_address}, got {from_address}"
                    )
        return v

    def pretty_print(self):
        for i, tx_result in enumerate(self.tx_results):
            status = "Successful" if not tx_result.error else "Failed"
            print(f"#{i + 1}: {status}")
            tx_result.pretty_print()
            print("-" * 40)


class SimulationError(Exception):
    """
    Error raised when simulation fails.

    Attributes:
        message (str): The error message.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


@tool
def simulate_transaction(transactions: List[TransactionParams]) -> SimulationResult:
    """
    Simulate a list of transactions to retrieve the asset changes and statuses.

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
    print(data)
    response = requests.post(url, json=data).json()

    if "error" in response:
        print(response)
        raise SimulationError(response["error"]["message"])
    if "result" in response:
        sender = transactions[0].from_address
        return _format_simulation_result(sender, response["result"])
    raise SimulationError(f"Unexpected response: {response}")


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
                raw_amount=asset.get("rawAmount", "0x0"),
                # from may be empty in some cases. e.g., 'mint'
                sender=asset.get("from", ""),
                receiver=asset.get("to", ""),
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
