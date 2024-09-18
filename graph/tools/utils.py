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


if __name__ == "__main__":
    assert convert_dec_to_hex.invoke({"integer": 11000}) == "0x2af8"
