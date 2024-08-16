from langchain_core.tools import tool
from langchain.pydantic_v1 import BaseModel


class Chain(BaseModel):
    id: int
    name: str


chains = {
    "arbitrum": Chain(id=42161, name="Arbitrum One"),
    "base": Chain(id=8453, name="Base"),
    "blast": Chain(id=81457, name="Blast"),
    "bsc": Chain(id=56, name="Binance Smart Chain"),
    "ethereum": Chain(id=1, name="Ethereum"),
    "linea": Chain(id=59144, name="Linea"),
    "optimism": Chain(id=10, name="Optimism"),
    "polygon": Chain(id=137, name="Polygon"),
    "scroll": Chain(id=534352, name="Scroll"),
}


@tool
async def get_chain_metadata(query: str) -> Chain:
    """
    Get the information of a chain. Throws an error if the chain is not found.
    Args:
        query (str): The chain name or chain ID.
    Returns:
        chain (Chain): The chain information
    """
    # TODO: Dummy implementation. Create a loader to fetch the data from a database.
    normalized_query = query.strip().lower()

    chain = chains.get(normalized_query)
    if not chain:
        raise ValueError(f"Unsupported chain: {query}")

    return chain
