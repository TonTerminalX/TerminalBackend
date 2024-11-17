import asyncio

from pytoniq import WalletV4R2
from pytoniq_core.crypto.keys import mnemonic_to_private_key, private_key_to_public_key
from pytoniq_core.crypto.signature import sign_message, verify_sign

from terminal_api.utils.client import get_client
from terminal_api.utils.tonapi import TonCenterApi


class WalletUtils:
    @staticmethod
    def get_public_key_bytes(address: str):
        # account_address = client
        # wallet = WalletV4(client, Address(address))
        # loop.run_until_complete(client.get_trusted_last_mc_block())
        # public_key = wallet.public_key
        # client.run_get_method(address, "get_public_key", [])
        public_key = TonCenterApi.run_get_method(address, "get_public_key", [])
        public_key = bytes.fromhex(public_key["stack"][0]["value"][2:])

        return public_key

        # hex_address = Address(address).to_str(is_user_friendly=False)
        # address = hex_address[2:]
        # _, public_key, _ = extract_public_key_from_address

    @staticmethod
    async def generate_wallet():
        # return await WalletV4.create(client, 0, None, version='v4r2')
        client = await get_client()
        mnemonic, new_wallet = await WalletV4R2.create(client)
        private_key = mnemonic_to_private_key(mnemonic)[1]
        await client.close()

        address = new_wallet.address.to_str(True)
        return new_wallet, address, private_key.hex(), private_key_to_public_key(private_key).hex(), " ".join(mnemonic)

    @staticmethod
    async def sign_message(message: str, private_key: str):
        client = await get_client()
        wallet = await WalletV4R2.from_private_key(client, bytes.fromhex(private_key))
        return sign_message(message.encode(), wallet.private_key)

    @staticmethod
    def verify_sign(public_key: bytes | str, message: str, sign: str):
        if isinstance(public_key, str):
            public_key = bytes.fromhex(public_key[2:])
        return verify_sign(public_key, message[2:].encode(), sign[2:].encode())


if __name__ == "__main__":
    wallet, address, private, public, mnemonic = asyncio.run(WalletUtils.generate_wallet())
    print(private, address, public, mnemonic)
    sign = asyncio.run(WalletUtils.sign_message("test, fuck it", private)).hex()
    print(sign)
    print(asyncio.run(WalletUtils.verify_sign(public, "test, fuck it", sign)))
