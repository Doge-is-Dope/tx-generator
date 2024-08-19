from langchain_core.tools import tool
from langchain.pydantic_v1 import BaseModel


async def transform_to_batch(query: str):
    """
    If the query requires multiple steps to accomplish, it can be transformed into a batch.
    Args:
        query (str): The query to transform.
    Returns:
        batch (str): The batch.
    """
    pass
