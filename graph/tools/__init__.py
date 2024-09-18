import os
from web3 import Web3

INFURA_API_KEY = os.getenv("INFURA_API_KEY")
w3 = Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"))


from graph.tools.abi import fetch_contract_abi, encode_function_call
from graph.tools.address import (
    resolve_ens,
    get_contract_address_by_name,
    convert_to_checksum_address,
)
from graph.tools.token import get_token_info, convert_to_smallest_unit
from graph.tools.time import get_current_timestamp, get_deadline
from graph.tools.utils import convert_dec_to_hex

tools = [
    fetch_contract_abi,
    encode_function_call,
    resolve_ens,
    get_contract_address_by_name,
    convert_to_checksum_address,
    get_token_info,
    convert_to_smallest_unit,
    convert_dec_to_hex,
    get_current_timestamp,
    get_deadline,
]
