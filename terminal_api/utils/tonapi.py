import asyncio

import base58
import requests
from pytoniq import Wallet, WalletV4R2, BaseWallet
from pytoniq_core import Address
from pytoniq_core.crypto.keys import mnemonic_to_private_key

from core import get_env_key


# from pytoniq_core.crypto.signature import


class TonCenterApi:
    api_url = "https://toncenter.com/api"
    _toncenter_key = get_env_key("TONCENTER_API_KEY")
    headers = {
        "X-Api-Key": _toncenter_key
    }

    account_info_endpoint = "/v3/addressInformation"
    run_get_method_endpoint = "/v3/runGetMethod"

    @classmethod
    def get_account_info(cls, address: str):
        response = requests.get(cls.api_url + cls.account_info_endpoint, params={
            "address": address,
            "use_v2": False,
        })
        response.raise_for_status()

        wallet_info = response.json()
        result = {
            "status": wallet_info["status"],
            "balance": int(wallet_info["balance"]) / 10 ** 9
        }
        return result

    @classmethod
    def run_get_method(cls, address: str, method: str, stack: list):
        body = {
            "address": address,
            "method": method,
            "stack": stack
        }
        response = requests.post(cls.api_url + cls.run_get_method_endpoint, json=body)
        response.raise_for_status()
        return response.json()
