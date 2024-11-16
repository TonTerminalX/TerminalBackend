import asyncio
import time

from pytoniq_core import Builder
from pytoniq_core.crypto.signature import sign_message

from terminal_api.utils.wallet import WalletUtils


# Create your tests here.
async def create_and_sign_message():
    print(2)
    wallet, address, private, public, mnemonic = await WalletUtils.generate_wallet()
    # message = ("test".encode() + address.to_str(is_user_friendly=False).encode() + "http://test.com".encode()
    #            + hex(int(time.time())).encode() + hex(1).encode())
    message = (
        Builder()
        .store_string("test")
        .store_string(address.to_str(is_user_friendly=False))
        .store_string("http://test.com")
        .store_uint(int(time.time()), 32)
        .store_uint(1, 8)
        .end_cell()
    )
    print(message)
    signed_message = sign_message(message, private)
    print(signed_message)


if __name__ == "__main__":
    print(1)
    asyncio.get_event_loop().run_until_complete(create_and_sign_message())
