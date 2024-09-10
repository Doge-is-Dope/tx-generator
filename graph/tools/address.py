import os
from typing import Optional
from functools import lru_cache
from langchain_core.tools import tool
from web3 import Web3
from ens import ENS


INFURA_API_KEY = os.getenv("INFURA_API_KEY")
w3 = Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"))
ns = ENS.from_web3(w3)


@lru_cache
def _resolve_ens(ens_name: str) -> Optional[str]:
    try:
        return ns.address(ens_name)
    except Exception as e:
        print(f"Error resolving {ens_name}: {e}")
        return None


@tool
def convert_to_checksum_address(address: str) -> str:
    """
    Convert an Ethereum address to its checksum version.

    Args:
        address (str): The Ethereum address to convert.

    Returns:
        str: The checksum address.
    """
    if not w3.is_address(address):
        raise ValueError(f"Invalid address: {address}")
    elif w3.is_checksum_address(address):
        return address
    return w3.to_checksum_address(address)


@tool
def resolve_ens(name: str) -> str:
    """
    Resolve the ENS name to an Ethereum address.

    Args:
        name (str): The ENS name to resolve.

    Returns:
        str: The Ethereum address if found, or an empty string.
    """
    if not name.endswith(".eth"):
        name = f"{name}.eth"
    return _resolve_ens(name)


import difflib


@tool
def get_contract_address_by_name(contract_name: str) -> str:
    """
    Retrieve the contract address for a given token or protocol by name.
    If the name is not found, it returns an empty string.

    Args:
        contract_name (str): The name of the token or protocol (e.g., 'stETH', 'Uniswap V2 Router').

    Returns:
        str: The corresponding contract address if found, otherwise an empty string.

    Example:
        exact match: get_contract_address_by_name.invoke('Uniswap') return the address for "uniswap_v2".
        partial match: get_contract_address_by_name.invoke('Uniswap V2 Router') return the address for "uniswap_v2".
        fuzzy match: get_contract_address_by_name.invoke('Uniswap V2 Routerr') return the address for "uniswap_v2".
    """

    # Hardcoded contract addresses for tokens and protocols, all keys are lowercase
    addresses = {
        # tokens
        "steth": "0xae7ab96520de3a18e5e111b5eaab095312d7fe84",  # stETH contract on Ethereum
        "usdc": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC contract on Ethereum
        "dai": "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI contract on Ethereum
        "usdt": "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT contract on Ethereum
        # protocols
        "uniswap_v2_router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap V2 Router
        "aave": "0x7D2768dE32b0b80b7a3454c06BdAcB11eBBeaFb5",  # Aave Lending Pool
        "compound": "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b",  # Compound Comptroller
        "lido": "0xae7ab96520de3a18e5e111b5eaab095312d7fe84",  # Lido Staked ETH
    }

    normalized_name = contract_name.lower()

    # Look for exact match first
    address = addresses.get(normalized_name)
    if address:
        return address

    # Perform partial matching (substring search)
    for name, addr in addresses.items():
        if normalized_name in name:
            return addr

    # Perform fuzzy matching for similar names
    possible_matches = difflib.get_close_matches(
        normalized_name, addresses.keys(), n=1, cutoff=0.6
    )
    if possible_matches:
        return addresses[possible_matches[0]]

    # Try to query the external resource if partial match also doesn't find any result
    address = _query_contract_address(normalized_name)
    if address:
        return address

    # Raise an error if the address is not found in either the cache or external resource
    raise ValueError(f"Contract address not found for name: {contract_name}")


def _query_contract_address(name: str) -> str:
    """
    TODO: Placeholder function to query an external resource (e.g., an API like Etherscan,
    CoinGecko, or The Graph) to resolve the contract address.

    Args:
        name (str): The name of the token or protocol.

    Returns:
        str: The contract address if found, otherwise an empty string.
    """
    import requests

    api_url = f"https://api.example.com/contracts?name={name}"

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            return data.get("contract_address", "")
        else:
            return ""
    except Exception as e:
        print(f"Error querying external resource: {e}")
        return ""


if __name__ == "__main__":
    res = get_contract_address_by_name.invoke("Uniswap")
    assert res == "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    res = get_contract_address_by_name.invoke("Uniswap V2 Router")
    assert res == "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    res = get_contract_address_by_name.invoke("Uniswap V2 Routerr")
    assert res == "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
