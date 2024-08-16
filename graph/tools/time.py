from datetime import datetime
from langchain_core.tools import tool


@tool
def get_current_timestamp() -> int:
    """
    Get the current timestamp. This is useful for calculating the deadline of a transaction.
    Returns:
        timestamp (int): The timestamp.
    """
    return datetime.now().timestamp()
