import datetime
import json
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import requests
from mplfinance.original_flavor import candlestick_ohlc


def merge_pairs_info(response: dict):
    merged_info = dict()
    for pair in response["data"]:
        merged_info[pair["relationships"]["base_token"]["data"]["id"]] = pair

    included = {}
    for pair in response["included"]:
        included[pair["id"]] = pair

    for token_id in included.keys():
        if token_id in merged_info:
            merged_info[token_id]["attributes"] = {
                **included[token_id]["attributes"],
                **merged_info[token_id]["attributes"],
            }

    return list(merged_info.values())


class GeckoTerminalApi:
    api_url = "https://api.geckoterminal.com/api/v2"
    get_ohlcv_data_endpoint = "/networks/{network}/pools/{pool}/ohlcv/day"
    get_trending_pairs_endpoint = "/networks/{network}/trending_pools?include=base_token%2Cquote_token%2Cdex&page=1"
    get_pair_endpoint = "/networks/{network}/pools/{pool}"

    default_pairs_path = Path(__file__).parent.parent.parent / "default_pairs.json"
    default_pairs = json.load(open(default_pairs_path, "r", encoding="utf-8"))

    headers = {"Accept": "application/json;version=20230302"}

    @classmethod
    def get_ohlcv_data(cls, pool_address: str):
        formater_endpoint = cls.get_ohlcv_data_endpoint.format(
            network="ton", pool=pool_address
        )
        response = requests.get(
            cls.api_url + formater_endpoint, headers=cls.headers, timeout=(10, 10)
        )
        response.raise_for_status()
        return response.json()["data"]["attributes"]["ohlcv_list"]

    @classmethod
    def get_trending_pairs(cls):
        endpoint = cls.api_url + cls.get_trending_pairs_endpoint.format(network="ton")
        response = requests.get(endpoint, headers=cls.headers, timeout=(10, 10))
        response.raise_for_status()
        return merge_pairs_info(response.json())

    @classmethod
    def get_pair(cls, pool: str):
        endpoint = f"{cls.api_url}{cls.get_pair_endpoint.format(network='ton', pool=pool)}"
        response = requests.get(endpoint, headers=cls.headers, timeout=(10, 10))
        response.raise_for_status()
        return response.json()["data"]


if __name__ == "__main__":
    api = GeckoTerminalApi()
    response = GeckoTerminalApi.get_trending_pairs()
    print(response)
    # chart = api.get_ohlcv_data("EQBCwe_IObXA4Mt3RbcHil2s4-v4YQS3wUDt1-DvZOceeMGO")

    # ohlc = [
    #     [
    #         mdates.date2num(datetime.datetime.utcfromtimestamp(item[0])),
    #         item[1],  # Open
    #         item[2],  # High
    #         item[3],  # Low
    #         item[4],  # Close
    #     ]
    #     for item in chart
    # ]

    # chart = api.get_ohlcv_data("EQBCwe_IObXA4Mt3RbcHil2s4-v4YQS3wUDt1-DvZOceeMGO")
    #
    # ohlc = [
    #     [
    #         mdates.date2num(datetime.datetime.utcfromtimestamp(item[0])),
    #         item[1],  # Open
    #         item[2],  # High
    #         item[3],  # Low
    #         item[4],  # Close
    #     ]
    #     for item in chart
    # ]
    #
    # volume = [item[5] for item in chart]
    # dates = [mdates.date2num(datetime.datetime.utcfromtimestamp(item[0])) for item in chart]
    # colors = ['g' if ohlc[i][4] >= ohlc[i][1] else 'r' for i in range(len(ohlc))]  # Цвета для объёмов
    #
    # # Построение графика
    # fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    #
    # # Свечной график
    # ax1.xaxis_date()
    # ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    # candlestick_ohlc(ax1, ohlc, width=0.6, colorup='g', colordown='r', alpha=0.8)
    # ax1.set_title("Candlestick Chart with Volume")
    # ax1.set_ylabel("Price")
    # ax1.grid()
    #
    # # Объём
    # ax2.bar(dates, volume, color=colors, width=0.6, alpha=0.8)
    # ax2.set_ylabel("Volume")
    # ax2.grid()
    #
    # # Общая настройка
    # plt.xlabel("Date")
    # plt.tight_layout()
    # plt.show()
