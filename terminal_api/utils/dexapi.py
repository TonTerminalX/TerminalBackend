import requests

from core import get_env_key


class DexScreenerApi:
    dexscreener_api = get_env_key("DEXSCREENER_API")
    search_pairs_endpoint = "/latest/dex/search"

    @classmethod
    def search_for_pairs(cls, search):
        response = requests.get(cls.dexscreener_api + cls.search_pairs_endpoint, params={
            "q": search,
        })
        response.raise_for_status()

        return response.json()
