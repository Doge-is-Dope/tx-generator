import time

from langchain_core.tools import tool


@tool
def get_current_timestamp() -> int:
    """
    Get the current Unix timestamp.

    Returns:
        int: The current Unix timestamp.
    """
    return int(time.time())


@tool
def get_deadline(delay: int = 3600) -> int:
    """
    Calculate the deadline for the transaction.

    Args:
        delay (int): The delay in seconds to add to the current timestamp. Default is 3600 seconds (1 hour).

    Returns:
        int: The calculated deadline for the transaction.
    """
    current_timestamp = get_current_timestamp.invoke({})
    return current_timestamp + delay


if __name__ == "__main__":
    from datetime import datetime

    timestamp = get_current_timestamp.invoke({})
    current_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current time: {current_time}")
