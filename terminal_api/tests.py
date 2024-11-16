import asyncio
import time

from pytoniq_core.crypto.signature import sign_message

from terminal_api.utils.tonapi import WalletUtils


# Create your tests here.
async def create_and_sign_message():
    wallet, address, private, public, mnemonic = await WalletUtils.generate_wallet()
    message = "test" + address + "http://test.com" + str(time.time()) + "1"
    signed_message = sign_message(message.encode("utf-8"), private)
    print(signed_message)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(create_and_sign_message())
