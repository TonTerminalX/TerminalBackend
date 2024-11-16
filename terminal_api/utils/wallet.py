import asyncio

from pytoniq import WalletV4R2
from pytoniq_core.crypto.keys import mnemonic_to_private_key, private_key_to_public_key

from terminal_api.utils.client import client


class WalletUtils:
    @staticmethod
    def get_public_key_bytes(address: str):
        # account_address = client
        # wallet = WalletV4(client, Address(address))
        loop = asyncio.get_event_loop()
        # loop.run_until_complete(client.get_trusted_last_mc_block())
        public_key = loop.run_until_complete(client.run_get_method_local(address, "get_public_key", []))
        public_key = hex(public_key[0])
        # public_key = wallet.public_key

        return public_key

        # hex_address = Address(address).to_str(is_user_friendly=False)
        # address = hex_address[2:]
        # _, public_key, _ = extract_public_key_from_address

    @staticmethod
    async def generate_wallet():
        # return await WalletV4.create(client, 0, None, version='v4r2')
        mnemonic, new_wallet = await WalletV4R2.create(client)
        private_key = mnemonic_to_private_key(mnemonic)[1]

        return new_wallet, new_wallet.address, private_key.hex(), private_key_to_public_key(private_key), mnemonic

    @staticmethod
    async def sign_message(message: str, private_key: str):
        wallet = WalletV4R2.from_private_key(client, private_key.encode())