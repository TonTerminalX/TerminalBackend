import requests

from core import get_env_key


class DexScreenerApi:
    dexscreener_api = "https://api.dexscreener.com"
    search_pairs_endpoint = "/latest/dex/search"
    get_pair_endpoint = "/latest/dex/pairs/{chain}/{pair}"
    get_new_pairs_endpoint = "/token-profiles/latest/v1"

    @classmethod
    def search_for_pairs(cls, search):
        response = requests.get(
            cls.dexscreener_api + cls.search_pairs_endpoint,
            params={
                "q": search,
            },
        )
        response.raise_for_status()

        return response.json()["pairs"]

    @classmethod
    def get_pair(cls, pair_address):
        response = requests.get(
            cls.dexscreener_api
            + cls.get_pair_endpoint.format(chain="ton", pair=pair_address)
        )
        response.raise_for_status()

        pairs = response.json()["pairs"]
        return pairs[0] if pairs else None

    @classmethod
    def get_new_pairs(cls):
        response = requests.get(cls.dexscreener_api + cls.get_new_pairs_endpoint)
        response.raise_for_status()

        return list(filter(lambda pair: pair["chainId"] == "ton", response.json()))


if __name__ == "__main__":
    # print(DexScreenerApi.get_pair("eqdyr9q8svyibjnyuptk13zmyb_iry3qdffpfciscawxucwi"))
    print(DexScreenerApi.search_for_pairs("DOGS")[0])
    DexScreenerApi.get_new_pairs()
