import os
from typing import Optional
from functools import lru_cache
from langchain_core.tools import tool
from web3 import Web3
from ens import ENS


infura_api_key = os.environ["INFURA_API_KEY"]
infura_url = f"https://mainnet.infura.io/v3/{infura_api_key}"
w3 = Web3(Web3.HTTPProvider(infura_url))
ns = ENS.from_web3(w3)


@lru_cache
def _resolve(ens_name: str) -> Optional[str]:
    try:
        return ns.address(ens_name)
    except Exception:
        return None


@tool
async def resolve_ens(name: str) -> Optional[str]:
    """
    Resolves an Ethereum Name Service (ENS) name to its corresponding Ethereum address.
    Args:
        name (str): The ENS name to be resolved.
    Returns:
        address (Optional[str]): The Ethereum address corresponding to the ENS name if it exists, otherwise `None`.
    """
    return _resolve(name)
