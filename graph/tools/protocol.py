import json
from typing import Dict, Any
from langchain_core.tools import tool


@tool
async def search_protocol(query: str) -> Dict:
    """
    Get the metadata of a DeFi protocol.
    This includes the protocol name, description and contract addresses deployed on the blockchain.
    """
    return {
        "name": "uniswap-v3",
        "category": "dex",
        "description": "Uniswap V3 is a decentralized exchange protocol that allows users to swap tokens.",
        "contracts": {
            "SwapRouter": {
                "description": "The SwapRouter contract is responsible for routing swaps between pools.",
                "addresses": {
                    "ethereum": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                    "arbitrum": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                    "optimism": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                },
            },
            "UniversalRouter": {
                "description": "The UniversalRouter contract is responsible for routing swaps between pools.",
                "addresses": {
                    "base": "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD",
                },
            },
        },
    }


@tool
async def get_contract_abi(chain: str, contract_address: str) -> Dict[str, Any]:
    """
    Retrieve the ABI (Application Binary Interface) of a smart contract given its address.
    ABI is a JSON representation of the contract's functions and events.
    This is useful for querying a contract's functions and its arguments for composing transactions.

    Args:
        contract_address (str): The address of the contract on the blockchain, represented as a hex string.
    Returns:
        str: The ABI of the contract in JSON format.
    """
    # TODO: When a user requests the ABI of a contract, fetch it from a database. If not found, fetch it from the blockchain and store it in the database.
    if contract_address == "0xE592427A0AEce92De3Edee1F18E0157C05861564":
        return json.loads("")
    return json.loads(
        '[{"constant":false,"inputs":[{"name":"newImplementation","type":"address"}],"name":"upgradeTo","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"newImplementation","type":"address"},{"name":"data","type":"bytes"}],"name":"upgradeToAndCall","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[],"name":"implementation","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"newAdmin","type":"address"}],"name":"changeAdmin","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"admin","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"inputs":[{"name":"_implementation","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"payable":true,"stateMutability":"payable","type":"fallback"},{"anonymous":false,"inputs":[{"indexed":false,"name":"previousAdmin","type":"address"},{"indexed":false,"name":"newAdmin","type":"address"}],"name":"AdminChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"implementation","type":"address"}],"name":"Upgraded","type":"event"}]'
    )
