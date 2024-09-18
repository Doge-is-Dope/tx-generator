import os
import requests
import json

from functools import lru_cache
from typing import Optional, List
from langchain_core.tools import tool

from graph.tools import w3
from graph.tools.address import convert_to_checksum_address

# Global cache for ABIs
_ABI_CACHE = {
    "erc20": None,
    "swap": None,
    "steth": None,  # stETH implementation contract
    # USDT
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": None,
    "usdt": None,
    # USDC
    "usdc": None,
}


def _load_abi_files():
    """
    Loads ABI files into the global ABI cache for reuse.
    """
    if not _ABI_CACHE["erc20"]:
        with open("abi/erc20.json") as file:
            _ABI_CACHE["erc20"] = json.load(file)

    if not _ABI_CACHE["swap"]:
        with open("abi/uniswap_v2_router.json") as file:
            _ABI_CACHE["swap"] = json.load(file)

    # Load any other frequently used ABIs here
    _ABI_CACHE["steth"] = _ABI_CACHE["erc20"]
    # USDT
    _ABI_CACHE["usdt"] = _ABI_CACHE["erc20"]
    _ABI_CACHE["0xdAC17F958D2ee523a2206206994597C13D831ec7"] = _ABI_CACHE["erc20"]
    # USDC
    _ABI_CACHE["usdc"] = _ABI_CACHE["erc20"]


_load_abi_files()  # Load the ABIs once when the module is loaded


@tool
def encode_function_call(abi: list, function_name: str, arguments: list) -> str:
    """
    Encode a smart contract function call into ABI-encoded data.

    This function takes the relevant function's ABI, the name of the function to call, and its arguments,
    and then returns the ABI-encoded data that can be included in the transaction's data field.

    Args:
        abi (str): The ABI of the contract in JSON format.
        function_name (str): The name of the contract function to call (e.g., 'approve').
        arguments (list): The arguments to the function as a list (e.g., [spender_address, amount]).

    Returns:
        str: The ABI-encoded data for the function call that can be used in a transaction.

    Example:
        data = encode_function_call(abi, 'approve', ['0xUniswapContractAddress', 400])
    """
    contract = w3.eth.contract(abi=abi)
    return contract.encode_abi(function_name, arguments)


@tool
def fetch_contract_abi(
    contract_address: str,
    contract_name: Optional[str] = None,
    contract_type: Optional[str] = None,
    function_name: Optional[str] = None,
) -> str:
    """
    Fetch the ABI (Application Binary Interface) for a given Ethereum contract address
    either from local cache or from the Etherscan API if not found locally.

    Args:
        contract_address (str): The Ethereum address of the smart contract.
        contract_name (str): The name of the contract (e.g., 'steth') to check local cache. Defaults to None.
        contract_type (str): The type of contract (e.g., 'swap') to check local cache. Defaults to None.
        function_name (str): The name of the function to be called. If provided, only the ABI for that function is returned.

    Returns:
        str: A JSON string representing the ABI of the contract.
    """
    # First try to fetch the ABI from local cache
    cached_abi = _fetch_cached_abi(
        contract_address=contract_address,
        contract_name=contract_name,
        contract_type=contract_type,
        function_name=function_name,
    )
    if cached_abi:
        return cached_abi

    # If no local ABI is available, fetch the ABI from the Etherscan API
    return _fetch_abi_from_remote(contract_address, function_name)


# Optimized function
@lru_cache
def _fetch_cached_abi(
    contract_address: str,
    contract_name: Optional[str] = None,
    contract_type: Optional[str] = None,
    function_name: Optional[str] = None,
) -> Optional[str]:
    """
    Fetches cached ABI for a specific contract address, name, or type.

    Args:
        contract_address (str): The contract address.
        contract_name (Optional[str], optional): The name of the contract.
        contract_type (Optional[str], optional): The type of the contract.
        function_name (Optional[str], optional): The specific function name ABI to retrieve.

    Returns:
        Optional[str]: The ABI or specific function ABI if found, otherwise None.
    """

    # Convert the contract address to checksum format
    checksum_address = convert_to_checksum_address.invoke(contract_address)
    # Normalize the contract name and type
    normalized_contract_name = contract_name.lower() if contract_name else None
    normalized_contract_type = contract_type.lower() if contract_type else None

    cache_keys = [
        checksum_address,  # Checksum contract address
        normalized_contract_name,  # Normalized contract name
        normalized_contract_type,  # Normalized contract type
    ]

    # Look up ABI in cache
    for key in cache_keys:
        if key and key in _ABI_CACHE:
            abi = _ABI_CACHE[key]
            break
    else:
        # No cached ABI found
        return None

    # If a specific function name is provided, extract the function's ABI
    if function_name:
        abi = _extract_function_abi(abi, function_name)

    return abi


def _extract_function_abi(abi: list, function_name: str) -> Optional[List]:
    """
    Extract the ABI entry for a specific function from the full contract ABI.

    Args:
        abi (list): The ABI of the contract in JSON format (as a list of ABI entries).
        function_name (str): The name of the function to extract.

    Returns:
        dict: The ABI entry for the specified function. Returns None if no function name is provided or if the function name is not found.
    """
    if not abi or not function_name:
        return None

    for entry in abi:
        if entry.get("type") == "function" and entry.get("name") == function_name:
            return [entry]
    return None


@lru_cache
def _fetch_abi_from_etherscan(address: str) -> dict:
    # print(f"Fetching ABI from Etherscan for address: {address}")
    etherscan_api_key = os.getenv("ETHERSCAN_API_KEY")
    etherscan_base_url = "https://api.etherscan.io/api"
    api_url = f"{etherscan_base_url}?module=contract&action=getabi&address={address}&apikey={etherscan_api_key}"
    response = requests.get(api_url)
    data = response.json()
    if data["status"] == "1":
        return json.loads(data["result"])
    else:
        raise ValueError(f"ABI not found: {data['result']}")


@lru_cache
def _fetch_abi_from_remote(
    contract_address: str,
    function_name: Optional[str] = None,
    max_redirects: int = 2,
) -> str:
    """
    Fetches ABI from the contract address and handles redirects for proxy contracts.

    Args:
        contract_address (str): The address of the contract.
        function_name (Optional[str], optional): The name of the function to search in the ABI. Defaults to None.
        max_redirects (int, optional): The maximum number of redirects to handle for proxy contracts. Defaults to 2.

    Returns:
        str: The contract ABI or function ABI.
    """
    current_address = contract_address

    for _ in range(max_redirects):
        # Fetch ABI from Etherscan
        abi = _fetch_abi_from_etherscan(current_address)

        # Check if the contract is a proxy contract
        if _extract_function_abi(abi, "implementation"):
            # print(f"Proxy contract detected at {current_address}")
            try:
                checksum_address = convert_to_checksum_address.invoke(current_address)

                # Try fetching cached ABI
                cached_abi = _fetch_cached_abi(contract_address=checksum_address)
                if cached_abi:
                    abi = cached_abi
                else:
                    # Fetch the implementation address via the contract call
                    implementation_address = (
                        w3.eth.contract(address=checksum_address, abi=abi)
                        .functions.implementation()
                        .call()
                    )
                    # print(f"Implementation address: {implementation_address}")
                    current_address = implementation_address
            except ValueError as e:  # Catch more specific errors like ValueError
                # print(f"Error fetching implementation address: {e}")
                break  # Exit if there's an error in fetching the implementation address
        else:
            # print("Not a proxy contract, returning the ABI")
            break  # Exit loop if no "implementation" function found (non-proxy contract)

    if function_name:
        return _extract_function_abi(abi, function_name) or abi

    return abi
