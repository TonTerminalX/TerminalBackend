import asyncio

from pytoniq import LiteClient


async def main():
    client = LiteClient.from_mainnet_config(  # choose mainnet, testnet or custom config dict
        ls_i=0,  # index of liteserver from config
        trust_level=2,  # trust level to liteserver
        timeout=15  # timeout not includes key blocks synchronization as it works in pytonlib
    )

    await client.connect()

    print(await client.get_masterchain_info())

    await client.reconnect()  # can reconnect to an exising object if had any errors

    await client.close()

    """ or use it with context manager: """
    async with LiteClient.from_mainnet_config(ls_i=0, trust_level=2, timeout=15) as client:
        await client.get_masterchain_info()

print(asyncio.run(main()))