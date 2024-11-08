import asyncio

import base58
import requests
from pytoniq import Wallet
from pytoniq_core import Address

from core import get_env_key
from terminal_api.utils.client import client
from pytoniq.contract.wallets import WalletV4
import secrets
import hashlib


# from pytoniq_core.crypto.signature import


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
        private_key = secrets.token_bytes(32)

        public_key = private_key.hex().encode('utf-8')
        public_key = hashlib.sha256(public_key).digest()
        public_key = base58.b58encode(public_key).decode('utf-8')

        addr_prefix = b'\x84\x87\x74\xef'
        addr_hash = hashlib.sha256(public_key.encode('utf-8')).digest()[:4]
        addr = addr_prefix + addr_hash + public_key.encode('utf-8')
        ton_address = base58.b58encode(addr).decode('utf-8')

        mnemonic = base58.b58encode(private_key).decode('utf-8')

        return ton_address, private_key, public_key, mnemonic


class TonCenterApi:
    api_url = get_env_key("TONCENTER_API")
    _toncenter_key = get_env_key("TONCENTER_API_KEY")
    headers = {
        "X-Api-Key": _toncenter_key
    }

    account_info_endpoint = "/v3/addressInformation"

    @classmethod
    def get_account_info(cls, address: str):
        response = requests.get(cls.api_url + cls.account_info_endpoint, params={
            "address": address,
            "use_v2": False,
        })
        response.raise_for_status()

        return response.json()


if __name__ == "__main__":
    print(WalletUtils.get_public_key_bytes("UQCMOXxD-f8LSWWbXQowKxqTr3zMY-X1wMTyWp3B-LR6syif"))
