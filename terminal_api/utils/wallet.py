import asyncio
import time
import typing

from dedust import (
    Asset,
    Factory,
    JettonRoot,
    PoolType,
    SwapParams,
    VaultJetton,
    VaultNative,
)
from pytoniq import LiteBalancer, LiteClient, LiteClientLike, WalletV4R2
from pytoniq.contract.wallets.wallet import WALLET_V4_R2_CODE
from pytoniq_core import Address, Cell, StateInit, begin_cell
from pytoniq_core.crypto.keys import (
    mnemonic_is_valid,
    mnemonic_new,
    mnemonic_to_private_key,
    private_key_to_public_key,
)
from pytoniq_core.crypto.signature import sign_message, verify_sign

from terminal_api.models import Transaction, User
from terminal_api.utils.client import get_client, get_lite_balancer
from terminal_api.utils.swap import DedustSwapModule
from terminal_api.utils.tonapi import TonCenterApi


def to_nano(amount: float | int):
    return int(amount * 10**9)


def from_nano(amount: float | int):
    return amount / 10**9


class CustomWallet(WalletV4R2):

    @classmethod
    async def from_address(
        cls, provider: LiteClientLike, address: typing.Union[str, Address], **kwargs
    ):
        if isinstance(address, str):
            address = Address(address)
        # account, shard_account = await provider.raw_get_account_state(address)
        account, shard_account = None, None
        return cls(
            provider=provider,
            address=address,
            account=account,
            shard_account=shard_account,
            **kwargs,
        )

    @classmethod
    async def from_state_init(
        cls, provider: LiteClientLike, workchain: int, state_init: StateInit, **kwargs
    ):
        address = Address((workchain, state_init.serialize().hash))
        return await cls.from_address(
            provider=provider, address=address, state_init=state_init, **kwargs
        )

    @classmethod
    async def from_data(
        cls,
        provider: LiteClientLike,
        public_key: bytes,
        wc: int = 0,
        wallet_id: typing.Optional[int] = None,
        **kwargs,
    ):
        return await super().from_code_and_data(
            provider=provider,
            code=WALLET_V4_R2_CODE,
            public_key=public_key,
            wc=wc,
            wallet_id=wallet_id,
            **kwargs,
        )

    @classmethod
    async def from_private_key(
        cls,
        provider: LiteClientLike,
        private_key: bytes,
        wc: int = 0,
        wallet_id: typing.Optional[int] = None,
        version: str = "v3r2",
    ):
        public_key = private_key_to_public_key(private_key)
        return await cls.from_data(
            provider=provider,
            wc=wc,
            public_key=public_key,
            wallet_id=wallet_id,
            private_key=private_key,
        )

    @classmethod
    async def from_mnemonic(
        cls,
        provider: LiteClientLike,
        mnemonics: typing.Union[list, str],
        wc: int = 0,
        wallet_id: typing.Optional[int] = None,
        version: str = "v3r2",
    ):
        version = cls.VERSION or version
        if isinstance(mnemonics, str):
            mnemonics = mnemonics.split()
        assert mnemonic_is_valid(mnemonics), "mnemonics are invalid!"
        _, private_key = mnemonic_to_private_key(mnemonics)
        return await cls.from_private_key(provider, private_key, wc, wallet_id, version)

    @classmethod
    async def create(
        cls,
        provider: LiteClientLike,
        wc: int = 0,
        wallet_id: typing.Optional[int] = None,
        version: str = "v3r2",
    ):
        """
        :param provider: provider
        :param wc: wallet workchain
        :param wallet_id: subwallet_id
        :param version: wallet version
        :return: mnemonics and Wallet instance of provided version
        """
        version = cls.VERSION or version
        mnemo = mnemonic_new(24)
        return mnemo, await cls.from_mnemonic(provider, mnemo, wc, wallet_id, version)


class WalletUtils(DedustSwapModule):
    DEFAULT_GAS = 0.25

    # client = asyncio.run(get_lite_balancer())
    # asyncio.run(client.start_up())
    # print(client.inited)
    # print(asyncio.run(client.get_account_state("UQCMOXxD-f8LSWWbXQowKxqTr3zMY-X1wMTyWp3B-LR6syif")))

    @staticmethod
    def get_public_key_bytes(address: str):
        # account_address = client
        # wallet = WalletV4(client, Address(address))
        # loop.run_until_complete(client.get_trusted_last_mc_block())
        # public_key = wallet.public_key
        # client.run_get_method(address, "get_public_key", [])
        try:
            public_key = TonCenterApi.run_get_method(address, "get_public_key", [])
            public_key = bytes.fromhex(public_key["stack"][0]["value"][2:])

            return public_key
        except ValueError as e:
            print(e)
            return None

        # hex_address = Address(address).to_str(is_user_friendly=False)
        # address = hex_address[2:]
        # _, public_key, _ = extract_public_key_from_address

    @staticmethod
    def to_user_friendly_address(address: str):
        return Address(address).to_str(is_bounceable=False)

    @classmethod
    async def generate_wallet(cls):
        client = LiteBalancer.from_mainnet_config()
        mnemonic, new_wallet = await CustomWallet.create(client)
        private_key = mnemonic_to_private_key(mnemonic)[1]

        address = new_wallet.address.to_str(is_user_friendly=True, is_bounceable=False)
        return (
            new_wallet,
            address,
            private_key.hex(),
            private_key_to_public_key(private_key).hex(),
            " ".join(mnemonic),
        )

    @staticmethod
    async def sign_message(message: str, private_key: str):
        # client = await get_client()
        client = await get_lite_balancer()
        wallet = await WalletV4R2.from_private_key(client, bytes.fromhex(private_key))
        await client.close_all()
        return sign_message(message.encode(), wallet.private_key)

    @staticmethod
    def verify_sign(public_key: bytes | str, message: str, sign: str):
        if isinstance(public_key, str):
            public_key = bytes.fromhex(public_key[2:])
        return verify_sign(public_key, message[2:].encode(), sign[2:].encode())

    @classmethod
    async def get_jetton_swap_params(
        cls,
        amount: int,
        jetton_address: str,
        recipient: str | Address,
        client: LiteBalancer,
    ):
        # query_id = 0  # idk what is this
        # # swap_id = 3926267997
        # deadline = 0
        # # limit = min_amount
        #
        # empty_cell = begin_cell().end_cell()
        # swap_params = (begin_cell()
        #                .store_uint(deadline, 32)
        #                .store_address(recipient)
        #                .store_address(None)
        #                .store_maybe_ref(None)
        #                .store_maybe_ref(None)
        #                .end_cell())
        #
        # dedust_swap_payload = (begin_cell()
        #                        .store_uint(cls.JETTON_SWAP_SELECTOR, 32)
        #                        .store_address(pool_address)
        #                        .store_uint(0, 1)
        #                        .store_coins(0)  # Slippage 100%
        #                        .store_maybe_ref(None)
        #                        .store_ref(swap_params)
        #                        .end_cell())
        #
        # jetton_transfer_and_swap = (begin_cell()
        #                             .store_uint(cls.JETTON_TRANSFER_SELECTOR, 32)
        #                             .store_uint(query_id, 64)
        #                             .store_coins(to_nano(amount))
        #                             .store_address(pool_address)
        #                             .store_address(recipient)
        #                             .store_maybe_ref(None)
        #                             .store_coins(to_nano(0.25))
        #                             .store_maybe_ref(dedust_swap_payload)
        #                             .end_cell())

        # contract_payload = (begin_cell()
        #                     .store_uint(cls.JETTON_SWAP_SELECTOR)
        #                     .store_uint(query_id, 64)
        #                     .store_coins(to_nano(amount))
        #                     .store_address(cls.SWAP_ADDRESS)
        #                     .store_address(recipient)
        #                     .store_maybe_ref(None)
        #                     .store_coins(to_nano(amount))
        #                     .store_maybe_ref(jetton_transfer_and_swap)
        #                     .end_cell())

        # return jetton_transfer_and_swap

        if isinstance(jetton_address, str):
            jetton_address = Address(jetton_address)

        # Create DeDust swap params and message
        jetton_asset = Asset.jetton(jetton_address)
        ton = Asset.native()
        # Get DeDust pool
        pool = await Factory.get_pool(PoolType.VOLATILE, [ton, jetton_asset], client)
        jetton_root: JettonRoot = JettonRoot.create_from_address(jetton_address)  # type: ignore
        jetton_vault = await Factory.get_jetton_vault(jetton_address, client)
        jetton_wallet = await jetton_root.get_wallet(recipient, client)

        # Create swap message with DeDust swap function invoke
        swap = jetton_wallet.create_transfer_payload(
            destination=jetton_vault.address,
            amount=amount,
            response_address=recipient,
            forward_amount=to_nano(cls.DEFAULT_GAS),
            forward_payload=VaultJetton.create_swap_payload(pool_address=pool.address),
        )
        return swap, jetton_wallet.address

    @classmethod
    def get_ton_swap_params(cls, amount: int, pool_address, recipient: str):
        deadline = int(time.time() + 1 * 60)
        query_id = 0
        limit = 0
        if isinstance(pool_address, str):
            pool_address = Address(pool_address)
        # swap_params = (
        #     begin_cell()
        #     .store_uint(deadline, 32)  # deadline
        #     .store_address(recipient)  # recipientAddress
        #     .store_address(None)  # referralAddress
        #     .store_maybe_ref(None)  # fulfillPayload
        #     .store_maybe_ref(None)  # rejectPayload
        #     .end_cell()
        # )
        #
        # # Payload to trigger the swap
        # native_vault_payload = (
        #     begin_cell()
        #     .store_uint(cls.TON_JETTON_SWAP, 32)
        #     .store_uint(query_id, 64)
        #     .store_coins(amount)
        #     .store_address(pool_address)
        #     .store_uint(0, 1)
        #     .store_coins(limit)
        #     .store_maybe_ref(None)
        #     .store_ref(swap_params)
        #     .end_cell()
        # )
        #
        # return native_vault_payload

        swap_params = SwapParams(deadline=deadline, recipient_address=recipient)
        swap = VaultNative.create_swap_payload(
            amount=amount, pool_address=pool_address, swap_params=swap_params
        )
        return swap

    @classmethod
    async def get_jetton_address(
        cls,
        client: LiteBalancer | LiteClient,
        address: str | Address,
        jetton_address: str | Address,
    ):
        if isinstance(address, str):
            address = Address(address)
        if isinstance(jetton_address, str):
            jetton_address = Address(jetton_address)

        print(address, jetton_address)
        _stack = begin_cell().store_address(address).end_cell().begin_parse()
        jetton_wallet_address = await client.run_get_method(
            address=jetton_address, method="get_wallet_address", stack=[_stack]
        )
        jetton_wallet_address = jetton_wallet_address[0].load_address()
        return jetton_wallet_address

    @classmethod
    async def activate_wallet(cls, wallet: WalletV4R2):
        tx_hash = wallet.transfer(
            destination=wallet.address, amount=0, state_init=None, body=Cell.empty()
        )
        return

    @classmethod
    async def wait_for_transaction(
        cls, client: LiteClient, address: str | Address, swap_send_time: float = None
    ):
        if isinstance(address, Address):
            address = address.to_str()

        toncenter = TonCenterApi()
        last_tx = toncenter.get_transactions(address, limit=1)
        last_tx_hash = last_tx[0]["transaction_id"]["hash"]
        # if last_tx.
        current_tx_hash = last_tx_hash

        start_time = time.time()
        end_time = start_time + 20
        while current_tx_hash == last_tx_hash:
            if time.time() > end_time:
                return None
            current_tx_hash = toncenter.get_transactions(address, limit=1)
            current_tx_hash = current_tx_hash[0]["transaction_id"]["hash"]
            await asyncio.sleep(1)

        return current_tx_hash

    @classmethod
    async def write_transaction_data(
        cls,
        client: LiteBalancer,
        address: str,
        is_ton_transfer: bool,
        jetton_address: str,
        pool_address: str,
    ):
        swap_send_time = time.time()
        user = User.find_user_by_wallet(address)
        tx_hash = cls.wait_for_transaction(client, address, swap_send_time)
        if not tx_hash:
            return

        transaction = Transaction(tx_hash=tx_hash)

    @classmethod
    async def make_swap(
        cls,
        pool_address: str,
        jetton_address: str | None,
        is_ton_transfer: bool,
        amount: float,
        mnemonic: str,
        slippage: int,
    ):
        # client = await get_client()
        balancer = await get_lite_balancer()
        # client = LiteClient.from_mainnet_config(timeout=20, ls_i=0)
        # await client.connect()
        wallet = await WalletV4R2.from_mnemonic(balancer, mnemonic)
        wallet_info = TonCenterApi.get_account_info(wallet.address)
        wallet_balance = wallet_info["balance"]

        # jetton_wallet_address = await cls.get_jetton_address(balancer, wallet.address, jetton_address)
        # print(f"Jetton wallet address ({wallet.address}): {jetton_wallet_address}")
        print(f"Wallet balance ({wallet.address}): {wallet_balance}")

        min_amount = cls.DEFAULT_GAS + 0.05
        pool_address = Address(pool_address).to_str(is_bounceable=True)
        if is_ton_transfer:
            ton_amount = amount
            swap_payload = cls.get_ton_swap_params(
                to_nano(ton_amount), pool_address, wallet.address
            )
            dest_address = cls.NATIVE_VAULT_ADDRESS
        else:
            ton_amount = min_amount
            swap_payload, jetton_wallet = await cls.get_jetton_swap_params(
                to_nano(amount), jetton_address, wallet.address, balancer
            )
            dest_address = Address(jetton_wallet.to_str())

        if min(wallet_balance, ton_amount) < min_amount:
            raise ValueError("Min amount")
        if wallet_balance < ton_amount:
            raise ValueError("Insufficient balance")

        dest_address = Address(dest_address)
        swap_message = wallet.create_wallet_internal_message(
            destination=dest_address,
            value=to_nano(ton_amount),
            body=swap_payload,
            state_init=None,
        )
        msgs = [swap_message]

        if (fee_amount := int(to_nano(ton_amount) * cls.SWAP_FEE)) > 1:
            fee_message = wallet.create_wallet_internal_message(
                destination=cls.SWAP_FEE_RECIPIENT,
                value=fee_amount,
                body=Cell.empty(),
                state_init=None,
            )
            msgs.append(fee_message)

        if wallet.is_uninitialized and not wallet.is_active:
            await wallet.send_init_external()

        swap_status = await wallet.raw_transfer(msgs=msgs)
        # swap_send_time = time.time()
        # tx_hash = cls.wait_for_transaction(balancer, wallet.address, swap_send_time)
        # await client.close()
        # await cls.write_transaction_data(balancer, wallet.address, is_ton_transfer,
        #                                  jetton_address, pool_address)
        await balancer.close_all()
        return swap_status


if __name__ == "__main__":
    client = asyncio.run(get_lite_balancer())
    asyncio.run(
        WalletUtils.wait_for_transaction(
            client, "UQCMOXxD-f8LSWWbXQowKxqTr3zMY-X1wMTyWp3B-LR6syif"
        )
    )
    # print(asyncio.run(test()))
    # client: LiteClient = asyncio.run(get_client())
    # print(asyncio.run(client.get_account_state("UQDhOY5FrggXpkbyKPbW76zLfwhfUW7IXrsrOg9gBVUmHGli")))
    # print(asyncio.run(WalletUtils.wait_for_transaction(client, "UQDhOY5FrggXpkbyKPbW76zLfwhfUW7IXrsrOg9gBVUmHGli")))
    # print(asyncio.run(client.get_account_state("UQBOO2tBR6N8TsU4RBHYaY5Mdss4hx3hJCEMFYYeZsd3xu1Z")))

    # wallet, address, private, public, mnemonic = asyncio.run(WalletUtils.generate_wallet())
    # print(private, address, public, mnemonic)
    # sign = asyncio.run(WalletUtils.sign_message("test", private)).hex()
    # print(sign)
    # print(asyncio.run(WalletUtils.verify_sign(public, "test", sign)))
