import time

from langchain_core.tools import tool


@tool
def convert_dec_to_hex(integer: int) -> str:
    """
    Convert an decimal integer to a hexadecimal string.

    Args:
        integer (int): The integer to be converted.

    Returns:
        str: The hexadecimal representation of the input integer, prefixed with '0x'.

    Example:
        hex_value = convert_int_to_hex(255)
        print(hex_value)  # Outputs: '0xff'
    """
    return hex(integer)


@tool
def get_current_timestamp() -> int:
    """
    Get the current Unix timestamp.

    Returns:
        int: The current Unix timestamp.
    """
    return int(time.time())


if __name__ == "__main__":
    from datetime import datetime

    timestamp = get_current_timestamp.invoke({})
    current_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current time: {current_time}")
    assert convert_dec_to_hex.invoke({"integer": 11000}) == "0x2af8"
