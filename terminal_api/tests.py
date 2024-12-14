import asyncio
import time

from pytoniq_core.crypto.signature import sign_message

from terminal_api.utils.client import get_lite_balancer
from terminal_api.utils.wallet import WalletUtils
from django.test import TestCase


class WalletTestCase(TestCase):
    async def create_and_sign_message(self):
        wallet, address, private, public, mnemonic = await WalletUtils.generate_wallet()
        message = "test" + address + "http://test.com" + str(time.time()) + "1"
        signed_message = sign_message(message.encode("utf-8"), private)
        print(signed_message)

    def test_lol(self):
        assert 1 == 1

    async def test_wallet_find_transaction(self):
        client = await get_lite_balancer()
        result = await WalletUtils.wait_for_transaction(client, "UQCMOXxD-f8LSWWbXQowKxqTr3zMY-X1wMTyWp3B-LR6syif")
