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
    jetton_wallets_endpoint = "/v3/jetton/wallets"
    run_get_method_endpoint = "/v3/runGetMethod"

    @classmethod
    def get_account_info(cls, address: str | Address):
        if isinstance(address, Address):
            address = address.to_str()
        params = {
            "address": address,
            "use_v2": False,
        }
        response = requests.get(cls.api_url + cls.account_info_endpoint, params=params)
        response.raise_for_status()

        wallet_info = response.json()
        print(wallet_info)
        result = {
            "status": wallet_info["status"],
            "balance": float(wallet_info["balance"]) / 10 ** 9
        }
        return result

    @classmethod
    def get_jetton_balance(cls, address: str, jetton_address: str):
        params = {
            "owner_address": [address],
            "jetton_address": [jetton_address],
            "limit": 1
        }
        response = requests.get(cls.api_url + cls.jetton_wallets_endpoint, params=params)
        response.raise_for_status()
        response_data = response.json()

        wallets = response_data["jetton_wallets"]
        balance = int(wallets[0]["balance"]) / 10 ** 9
        return balance


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


if __name__ == "__main__":
    print(TonCenterApi.get_account_info("EQDhOY5FrggXpkbyKPbW76zLfwhfUW7IXrsrOg9gBVUmHDSn"))
    print(TonCenterApi.get_account_info("UQCMOXxD-f8LSWWbXQowKxqTr3zMY-X1wMTyWp3B-LR6syif"))
