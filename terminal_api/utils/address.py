from pytoniq_core import Address, AddressError


def is_valid_address(address: str):
    try:
        return bool(Address(address))
    except AddressError as e:
        return False
