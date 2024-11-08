import asyncio
from pytoniq import LiteClient, LiteBalancer

client: LiteClient = LiteClient.from_mainnet_config(7)
asyncio.get_event_loop().run_until_complete(client.connect())
