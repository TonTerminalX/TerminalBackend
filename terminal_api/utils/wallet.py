import asyncio

from pytoniq import WalletV4R2
from pytoniq_core import Cell, begin_cell, Address
from pytoniq_core.crypto.keys import mnemonic_to_private_key, private_key_to_public_key
from pytoniq_core.crypto.signature import sign_message, verify_sign

from terminal_api.utils.client import get_client
from terminal_api.utils.tonapi import TonCenterApi

def to_nano(amount: float | int):
    return int(amount * 10 ** 9)


class WalletUtils:
    JETTON_SWAP_SELECTOR = 3818968194
    JETTON_TRANSFER_SELECTOR = 260734629
    SWAP_ADDRESS = Address("EQCo_dAv39DAV62oG5HIC_nVeVjIaVZi-Zmlzjbx8AoPqjZb")

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
        await client.close()
        return sign_message(message.encode(), wallet.private_key)

    @staticmethod
    def verify_sign(public_key: bytes | str, message: str, sign: str):
        if isinstance(public_key, str):
            public_key = bytes.fromhex(public_key[2:])
        return verify_sign(public_key, message[2:].encode(), sign[2:].encode())

    @classmethod
    def get_jetton_swap_params(cls, amount: float, pool_address: str, recipient: str):
        query_id = 0  # idk what is this
        # swap_id = 3926267997
        deadline = 0
        # limit = min_amount

        empty_cell = begin_cell().end_cell()
        swap_params = (begin_cell()
                       .store_uint(deadline, 32)
                       .store_address(recipient)
                       .store_address(recipient)
                       .store_maybe_ref(empty_cell)
                       .store_maybe_ref(empty_cell)
                       .end_cell())

        dedust_swap_payload = (begin_cell()
                               .store_uint(cls.JETTON_SWAP_SELECTOR, 32)
                               .store_coins(to_nano(amount))
                               .store_address(pool_address)
                               .store_uint(0, 1)
                               .store_coins(0)  # Slippage 100%
                               .store_maybe_ref(None)
                               .store_ref(swap_params)
                               .end_cell())

        jetton_transfer_and_swap = (begin_cell()
                                    .store_uint(cls.JETTON_TRANSFER_SELECTOR, 32)
                                    .store_uint(query_id, 64)
                                    .store_coins(to_nano(amount))
                                    .store_address(pool_address)
                                    .store_address(recipient)
                                    .store_coins(to_nano(0.25))
                                    .store_maybe_ref(dedust_swap_payload)
                                    .end_cell())

        contract_payload = (begin_cell()
                            .store_uint(cls.JETTON_SWAP_SELECTOR)
                            .store_uint(query_id, 64)
                            .store_coins(to_nano(amount))
                            .store_address(cls.SWAP_ADDRESS)
                            .store_address(recipient)
                            .store_maybe_ref(None)
                            .store_coins(to_nano(amount))
                            .store_maybe_ref(jetton_transfer_and_swap)
                            .end_cell())

        return contract_payload


    @classmethod
    def get_ton_swap_params(cls, amount: float, pool_address, recipient: str):
        deadline = 0
        query_id = 0
        limit = 0
        swap_params = (
            begin_cell()
            .store_uint(deadline, 32)  # deadline
            .store_address(None)  # recipientAddress
            .store_address(None)  # referralAddress
            .store_maybe_ref(None)  # fulfillPayload
            .store_maybe_ref(None)  # rejectPayload
            .end_cell()
        )

        # Payload to trigger the swap
        native_vault_payload = (
            begin_cell()
            .store_uint(cls.JETTON_SWAP_SELECTOR, 32)
            .store_uint(query_id, 64)
            .store_coins(amount)
            .store_address(pool_address)
            .store_uint(0, 1)
            .store_coins(limit)
            .store_maybe_ref(None)
            .store_ref(swap_params)
            .end_cell()
        )

        return native_vault_payload

    @classmethod
    async def get_jetton_address(cls, client, address: str, jetton_address: str):
        _stack = begin_cell().store_address(address).end_cell().begin_parse()
        jetton_wallet_address = await client.run_get_method(address=jetton_address, method="get_wallet_address",
                                                            stack=_stack)
        jetton_wallet_address = jetton_wallet_address[0].load_address()
        return jetton_wallet_address

    @classmethod
    async def make_swap(cls, pool_address: str, jetton_address: str | None, is_ton_transfer: bool,
                        amount: float, private_key: str):
        client = await get_client()
        wallet = await WalletV4R2.from_private_key(client, bytes.fromhex(private_key))
        jetton_wallet_address = await cls.get_jetton_address(client, wallet.address, jetton_address)
        print(f"Jetton wallet address ({wallet.address}): {jetton_wallet_address}")
        await client.close()

        if is_ton_transfer:
            ton_amount = amount
            swap_payload = cls.get_ton_swap_params(ton_amount, pool_address, wallet.address).to_boc()
            dest_address = pool_address
        else:
            ton_amount = 0.1
            swap_payload = cls.get_jetton_swap_params(amount, pool_address, wallet.address).to_boc()
            dest_address = jetton_address

        swap_tx = await wallet.transfer(dest_address, amount=to_nano(ton_amount), body=swap_payload)
        print(swap_tx, type(swap_tx))
        return swap_tx


async def test():
    client = await get_client()
    address = Address("UQBOO2tBR6N8TsU4RBHYaY5Mdss4hx3hJCEMFYYeZsd3xu1Z")
    address1 = Address("EQBC7TfBl0EAuO6k_w0NUCURfItDGzTyfTJ1JlfxShN1HaNd")
    jetton_address = Address("EQB02DJ0cdUD4iQDRbBv4aYG3htePHBRK1tGeRtCnatescK0")

    _stack = begin_cell().store_address(address).end_cell().begin_parse()
    jetton_wallet_address = await client.run_get_method(address=jetton_address, method="get_wallet_address",
                                                        stack=[_stack])
    jetton_wallet_address = jetton_wallet_address[0].load_address()
    print(f"Jetton wallet address ({address}): {jetton_wallet_address}")
    print(address1)


if __name__ == "__main__":
    print(asyncio.run(test()))
    # wallet, address, private, public, mnemonic = asyncio.run(WalletUtils.generate_wallet())
    # print(private, address, public, mnemonic)
    # sign = asyncio.run(WalletUtils.sign_message("test", private)).hex()
    # print(sign)
    # print(asyncio.run(WalletUtils.verify_sign(public, "test", sign)))
