import asyncio

import base58
import requests
from pytoniq import Wallet, WalletV4R2, BaseWallet
from pytoniq_core import Address
from pytoniq_core.crypto.keys import mnemonic_to_private_key

from core import get_env_key
from terminal_api.utils.client import client
from pytoniq.contract.wallets import WalletV4
import secrets
import hashlib

from terminal_api.utils.wallet import WalletUtils


# from pytoniq_core.crypto.signature import


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
    print(asyncio.get_event_loop().run_until_complete(WalletUtils.generate_wallet()))
