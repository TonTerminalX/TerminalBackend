import asyncio
from pytoniq import LiteClient, LiteBalancer


async def get_client():
    client: LiteClient = LiteClient.from_mainnet_config(
        ls_i=0,
        # trust_level=2,
        timeout=20
    )
    await client.connect()
    return client


async def get_lite_balancer():
    balancer = LiteBalancer.from_mainnet_config(timeout=10)
    await balancer.start_up()
    return balancer


async def _test():
    client = await get_client()
    balancer = await get_lite_balancer()
    await client.get_masterchain_info()
    await balancer.get_masterchain_info()


if __name__ == "__main__":
    asyncio.run(_test())
