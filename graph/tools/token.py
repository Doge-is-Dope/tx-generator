from langchain_core.tools import tool

from graph.tools.abi import fetch_contract_abi
from graph.tools.address import convert_to_checksum_address
from graph.tools import w3


@tool
def get_token_info(token_address: str) -> dict:
    """
    Retrieve the token information (symbol, name, decimals) from an ERC-20 token contract.

    Args:
        token_address (str): The Ethereum address of the token contract.

    Returns:
        dict: A dictionary containing the token's symbol, name, and decimals.

    Example:
        token_info = get_token_info('0xae7ab96520de3a18e5e111b5eaab095312d7fe84')
        print(token_info)  # Outputs: {'decimals': 18, 'symbol': 'stETH', 'name': 'Lido Staked Ether'}
    """
    # Create the contract object
    contract = w3.eth.contract(
        address=convert_to_checksum_address.invoke(token_address),
        abi=fetch_contract_abi.invoke(
            {"contract_address": token_address, "contract_type": "erc20"}
        ),
    )

    with w3.batch_requests() as batch:
        batch.add(contract.functions.symbol())
        batch.add(contract.functions.name())
        batch.add(contract.functions.decimals())
        responses = batch.execute()

    return {
        "symbol": responses[0],
        "name": responses[1],
        "decimals": responses[2],
    }


@tool
def convert_to_smallest_unit(amount: str, decimals: int) -> int:
    """
    Convert a token amount to its smallest unit (wei-like amount), preserving precision.

    Args:
        amount (float): The amount to convert as a string to preserve precision.
        decimals (int): The number of decimals the token uses (e.g., 18 for stETH).

    Returns:
        int: The token amount in the smallest unit (e.g., wei for stETH).

    Example:
        token_amount = convert_to_token_amount('0.299999999999999997', 18)
        print(token_amount)  # Outputs: 299999999999999997
    """
    from decimal import Decimal

    amount_decimal = Decimal(amount)

    return int(amount_decimal * (10**decimals))
