import asyncio
from pytoniq import LiteClient, LiteBalancer


async def get_client():
    client: LiteClient = LiteClient.from_mainnet_config(
        ls_i=0,
        trust_level=2,
        timeout=15
    )
    await client.connect()
    return client


async def test_func():
    client: LiteClient = await (get_client())
    result = await (
        client.run_get_method("UQBmzW4wYlFW0tiBgj5sP1CgSlLdYs-VpjPWM7oPYPYWQBqW", "get_public_key", []))

    print(result)
    key = hex(result[0])
    print(key)
    return bytes.fromhex(key[2:])

if __name__ == "__main__":
    print(asyncio.run(test_func()))
