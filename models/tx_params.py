from pydantic import BaseModel, Field, field_validator


class TransactionParams(BaseModel):
    """
    Parameters for a blockchain transaction.

    Attributes:
        from_address (str): Sender's address, must start with '0x' and be 42 characters long.
        to_address (str): Recipient's address or contract address, must start with '0x' and be 42 characters long.
        data (str): Transaction data in hexadecimal format, must start with '0x'.
        value (str): Native token amount in hexadecimal format, must start with '0x'.

    Validation:
        - Addresses (`from_address`, `to_address`) must be valid hex strings starting with '0x' and 42 characters in length.
        - `value` and `data` must start with '0x'.

    Purpose:
        Ensures correct formatting of transaction parameters before submission to the blockchain.
    """

    from_address: str = Field(description="The address of the sender (from)")
    to_address: str = Field(description="The address being interacted with (to)")
    data: str = Field("0x", description="Transaction data in hex, start with '0x'")
    value: str = Field("0x0", description="Amount of native token to send, in hex")

    @field_validator("from_address", "to_address")
    def check_address_format(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Address must start with '0x'")
        if len(v) != 42:
            raise ValueError("Address must be 42 characters long")
        return v

    @field_validator("value")
    def check_value_format(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Value must start with '0x'")
        return v

    @field_validator("data")
    def check_data_format(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Data must start with '0x'")
        return v

    def __str__(self):
        return f"From: {self.from_address}\nTo: {self.to_address}\nData: {self.data}\nValue: {self.value}"
