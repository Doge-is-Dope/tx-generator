from typing import Optional, Union
from langchain_core.tools import tool
from langchain.pydantic_v1 import BaseModel, Field


# TODO: Token addresses mapped by chain. Shall be fetched from a database.
token_data = {
    "usdc": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6,
        "address": {
            "ethereum": {
                "chain_id": 1,
                "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            },
            "polygon": {
                "chain_id": 137,
                "address": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
            },
            "base": {
                "chain_id": 1,
                "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            },
        },
    },
    "usdt": {
        "name": "Tether USD",
        "symbol": "USDT",
        "decimals": 6,
        "address": {
            "ethereum": {
                "chain_id": 1,
                "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
            },
            "polygon": {
                "chain_id": 137,
                "address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
            },
        },
    },
}


class Erc20(BaseModel):
    name: str = Field(str, description="The token name")
    symbol: str = Field(str, description="The token symbol")
    decimals: int = Field(int, description="The number of decimals of the token")
    chain_id: int = Field(int, description="The chain ID where the token is deployed")
    address: str = Field(str, description="The contract address of the token")


@tool
async def get_erc20_metadata(token: str, chain: str) -> Optional[Erc20]:
    """
    Fetch the ERC20 token information including the name, symbol, decimals, chain ID, and contract address.
    Args:
        token (str): The token symbol or name.
        chain (str): The chain name or chain ID.
    Returns:
        erc20 (Erc20): The ERC-20 token information or None if the token is not found.
    """
    # TODO: Dummy implementation. Create a loader to fetch the data from a database.
    normalized_token = token.strip().lower()
    normalized_chain = chain.strip().lower()
    token_info = token_data.get(normalized_token)
    if token_info:
        chain_info = token_info.get("address", {}).get(normalized_chain)
        if chain_info:
            return Erc20(
                name=token_info["name"],
                symbol=token_info["symbol"],
                decimals=token_info["decimals"],
                chain_id=chain_info["chain_id"],
                address=chain_info["address"],
            )
    return None
